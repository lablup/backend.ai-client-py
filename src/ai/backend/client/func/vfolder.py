import asyncio
from pathlib import Path
from sys import modules
from typing import (
    Mapping,
    Sequence,
    Union,
    Any,
)

import aiohttp
import janus
from tqdm import tqdm
from multidict import CIMultiDict

from yarl import URL
from aiotusclient import client

from ai.backend.client.output.fields import vfolder_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from .base import api_function, BaseFunction
from ..exceptions import BackendClientError
from ..compat import current_loop
from ..config import DEFAULT_CHUNK_SIZE, MAX_INFLIGHT_CHUNKS
from ..pagination import generate_paginated_results
from ..request import Request

__all__ = (
    'VFolder',
)

_default_list_fields = (
    vfolder_fields['host'],
    vfolder_fields['name'],
    vfolder_fields['created_at'],
    vfolder_fields['creator'],
    vfolder_fields['group_id'],
    vfolder_fields['permission'],
    vfolder_fields['ownership_type'],
)

class VFolder(BaseFunction):

    def __init__(self, name: str):
        self.name = name

    @api_function
    @classmethod
    async def create(
        cls,
        name: str,
        host: str = None,
        unmanaged_path: str = None,
        group: str = None,
        usage_mode: str = 'general',
        permission: str = 'rw',
        quota: str = '0',
        cloneable: bool = False,
    ):
        rqst = Request('POST', '/folders')
        rqst.set_json({
            'name': name,
            'host': host,
            'unmanaged_path': unmanaged_path,
            'group': group,
            'usage_mode': usage_mode,
            'permission': permission,
            'quota': quota,
            'cloneable': cloneable,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_by_id(cls, oid):
        rqst = Request('DELETE', '/folders')
        rqst.set_json({'id': oid})
        async with rqst.fetch():
            return {}

    @api_function
    @classmethod
    async def list(cls, list_all=False):
        rqst = Request('GET', '/folders')
        rqst.set_json({'all': list_all})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        group: str = None,
        access_key: str = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of vfolders. Domain admins can only get domain vfolders.

        :param group: Fetch vfolders in a specific group.
        :param fields: Additional per-vfolder query fields to fetch.
        """
        return await generate_paginated_results(
            'vfolder_list',
            {
                'group_id': (group, 'UUID'),
                'access_key': (access_key, 'String'),
                'filter': (filter, 'String'),
                'order': (order, 'String'),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def list_hosts(cls):
        rqst = Request('GET', '/folders/_/hosts')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_all_hosts(cls):
        rqst = Request('GET', '/folders/_/all_hosts')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_allowed_types(cls):
        rqst = Request('GET', '/folders/_/allowed_types')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def info(self):
        rqst = Request('GET', '/folders/{0}'.format(self.name))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request('DELETE', '/folders/{0}'.format(self.name))
        async with rqst.fetch():
            return {}

    @api_function
    async def rename(self, new_name):
        rqst = Request('POST', '/folders/{0}/rename'.format(self.name))
        rqst.set_json({
            'new_name': new_name,
        })
        async with rqst.fetch() as resp:
            self.name = new_name
            return await resp.text()

    @api_function
    async def download(
        self,
        relative_paths: Sequence[Union[str, Path]],
        *,
        basedir: Union[str, Path] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        show_progress: bool = False,
        max_retry: int = 3,
    ) -> None:
        base_path = (Path.cwd() if basedir is None else Path(basedir).resolve())
        for relpath in relative_paths:
            file_path = base_path / relpath
            if file_path.exists():
                raise RuntimeError('The target file already exists', file_path.name)
            rqst = Request('POST',
                           '/folders/{}/request-download'.format(self.name))
            rqst.set_json({
                'path': str(relpath),
            })
            async with rqst.fetch() as resp:
                download_info = await resp.json()
                download_url = URL(download_info['url']).with_query({
                    'token': download_info['token'],
                })

            if show_progress:
                print(f"Downloading to {file_path} ...")
            async with aiohttp.ClientSession() as client:
                retry_config = {
                    'retry_cnt': 0,
                    'retry_available': False,
                    'is_retry': False,
                    'content_range': 0,
                    'range_unit': None,
                    'ir_validator': None,
                }
                retry_hdrs = {
                    'If-Range': None,
                    'Range': None
                }
                async def try_download(
                    client: aiohttp.ClientSession,
                    download_url: URL,
                    rqst_hdrs: CIMultiDict,
                    retry_config: Mapping[str, Any]
                ) -> None:
                    async with client.get(download_url, ssl=False, headers=rqst_hdrs) as raw_resp:
                        size = int(raw_resp.headers['Content-Length'])
                        range_unit = raw_resp.headers.get('Accept-Ranges')
                        last_modified = raw_resp.headers.get('Last-Modified')
                        etag = raw_resp.headers.get('Etag')
                        ir_validator = last_modified if last_modified is not None else etag
                        if not retry_config['is_retry'] and range_unit is not None and \
                            ir_validator is not None:
                            retry_config['range_unit'] = range_unit
                            retry_config['ir_validator'] = ir_validator
                            retry_config['retry_available'] = True
                        q: janus.Queue[bytes] = janus.Queue(MAX_INFLIGHT_CHUNKS)

                        def _write_file(file_path: Path, q: janus._SyncQueueProxy[bytes], mode: str):
                            with open(file_path, mode) as f:
                                while True:
                                    chunk = q.get()
                                    if not chunk:
                                        return
                                    f.write(chunk)
                                    q.task_done()

                        try:
                            with tqdm(
                                total=size,
                                unit=range_unit,
                                unit_scale=True,
                                unit_divisor=1024,
                                disable=not show_progress,
                            ) as pbar:
                                loop = current_loop()
                                mode = 'wb' if not retry_config['is_retry'] else 'ab'
                                writer_fut = loop.run_in_executor(None, _write_file, file_path, q.sync_q, mode)
                                await asyncio.sleep(0)
                                while True:
                                    chunk = await raw_resp.content.read(chunk_size)
                                    retry_config['content_range'] += len(chunk)
                                    pbar.update(len(chunk))
                                    if not chunk:
                                        break
                                    await q.async_q.put(chunk)
                        finally:
                            await q.async_q.put(b'')
                            await writer_fut
                            q.close()
                            await q.wait_closed()
                while True:
                    try:
                        rqst_hdrs = client.headers
                        if retry_config['is_retry']:
                            rqst_hdrs.extend(retry_hdrs)
                        await try_download(client, download_url, rqst_hdrs, retry_config)
                        break
                    except aiohttp.ClientConnectionError as e:
                        if retry_config['retry_cnt'] == max_retry or not retry_config['retry_available']:
                            msg = 'Request to the API endpoint has failed.\n' \
                                'Check your network connection and/or the server status.\n' \
                                '\u279c {!r}'.format(e)
                            raise BackendClientError(msg) from e
                        retry_config['retry_cnt'] += 1
                        retry_hdrs['If-Range'] = retry_config['ir_validator']
                        retry_hdrs['Range'] = f'{retry_config["range_unit"]}={retry_config["content_range"]}-'
                        retry_config['is_retry'] = True
                        continue
                    except aiohttp.ClientResponseError as e:
                        msg = 'API endpoint response error.\n' \
                            '\u279c {!r}'.format(e)
                        raise BackendClientError(msg) from e
                    except InterruptedError as e:
                        # Handle something?
                        raise e


    @api_function
    async def upload(
        self,
        files: Sequence[Union[str, Path]],
        *,
        basedir: Union[str, Path] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        show_progress: bool = False,
    ) -> None:
        base_path = (Path.cwd() if basedir is None else Path(basedir).resolve())
        if basedir:
            files = [basedir / Path(file) for file in files]
        else:
            files = [Path(file).resolve() for file in files]
        for file_path in files:
            file_size = Path(file_path).stat().st_size
            rqst = Request('POST',
                           '/folders/{}/request-upload'.format(self.name))
            rqst.set_json({
                'path': "{}".format(str(Path(file_path).relative_to(base_path))),
                'size': int(file_size),
            })
            async with rqst.fetch() as resp:
                upload_info = await resp.json()
                upload_url = URL(upload_info['url']).with_query({
                    'token': upload_info['token'],
                })
            tus_client = client.TusClient()
            if basedir:
                input_file = open(base_path / file_path, "rb")
            else:
                input_file = open(str(Path(file_path).relative_to(base_path)), "rb")
            print(f"Uploading {base_path / file_path} via {upload_info['url']} ...")
            # TODO: refactor out the progress bar
            uploader = tus_client.async_uploader(
                file_stream=input_file,
                url=upload_url,
                upload_checksum=False,
                chunk_size=chunk_size,
            )
            return await uploader.upload()

    @api_function
    async def mkdir(self, path: Union[str, Path]):
        rqst = Request('POST',
                       '/folders/{}/mkdir'.format(self.name))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    async def rename_file(self, target_path: str, new_name: str):
        rqst = Request('POST',
                       '/folders/{}/rename_file'.format(self.name))
        rqst.set_json({
            'target_path': target_path,
            'new_name': new_name,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete_files(self,
                           files: Sequence[Union[str, Path]],
                           recursive: bool = False):
        rqst = Request('DELETE',
                       '/folders/{}/delete_files'.format(self.name))
        rqst.set_json({
            'files': files,
            'recursive': recursive,
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    async def list_files(self, path: Union[str, Path] = '.'):
        rqst = Request('GET', '/folders/{}/files'.format(self.name))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def invite(self, perm: str, emails: Sequence[str]):
        rqst = Request('POST', '/folders/{}/invite'.format(self.name))
        rqst.set_json({
            'perm': perm, 'user_ids': emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def invitations(cls):
        rqst = Request('GET', '/folders/invitations/list')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def accept_invitation(cls, inv_id: str):
        rqst = Request('POST', '/folders/invitations/accept')
        rqst.set_json({'inv_id': inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_invitation(cls, inv_id: str):
        rqst = Request('DELETE', '/folders/invitations/delete')
        rqst.set_json({'inv_id': inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_fstab_contents(cls, agent_id=None):
        rqst = Request('GET', '/folders/_/fstab')
        rqst.set_json({
            'agent_id': agent_id,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_performance_metric(cls, folder_host: str):
        rqst = Request('GET', '/folders/_/perf-metric')
        rqst.set_json({
            'folder_host': folder_host,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_mounts(cls):
        rqst = Request('GET', '/folders/_/mounts')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def mount_host(cls, name: str, fs_location: str, options=None,
                         edit_fstab: bool = False):
        rqst = Request('POST', '/folders/_/mounts')
        rqst.set_json({
            'name': name,
            'fs_location': fs_location,
            'options': options,
            'edit_fstab': edit_fstab,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def umount_host(cls, name: str, edit_fstab: bool = False):
        rqst = Request('DELETE', '/folders/_/mounts')
        rqst.set_json({
            'name': name,
            'edit_fstab': edit_fstab,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def share(self, perm: str, emails: Sequence[str]):
        rqst = Request('POST', '/folders/{}/share'.format(self.name))
        rqst.set_json({
            'permission': perm, 'emails': emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def unshare(self, emails: Sequence[str]):
        rqst = Request('DELETE', '/folders/{}/unshare'.format(self.name))
        rqst.set_json({
            'emails': emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def leave(self):
        rqst = Request('POST', '/folders/{}/leave'.format(self.name))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def clone(self, target_name: str, target_host: str = None,
                    usage_mode: str = 'general', permission: str = 'rw'):
        rqst = Request('POST', '/folders/{}/clone'.format(self.name))
        rqst.set_json({
            'target_name': target_name,
            'target_host': target_host,
            'usage_mode': usage_mode,
            'permission': permission,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def update_options(self, name: str, permission: str = None,
                             cloneable: bool = None):
        rqst = Request('POST', '/folders/{}/update-options'.format(self.name))
        rqst.set_json({
            'cloneable': cloneable,
            'permission': permission,
        })
        async with rqst.fetch() as resp:
            return await resp.text()
