from pathlib import Path
from typing import (
    Sequence, List,
    cast, Mapping, Union
)

from datetime import datetime
from dateutil.tz import tzutc


import aiohttp
from aiohttp import hdrs
from tqdm import tqdm

from yarl import URL
from .base import api_function, BaseFunction
from ..compat import current_loop
from ..config import DEFAULT_CHUNK_SIZE
from ..exceptions import BackendAPIError
from ..request import Request
from ..session import api_session

from .tusclient import client

__all__ = (
    'VFolder',
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
    ):
        rqst = Request(api_session.get(), 'POST', '/folders')
        rqst.set_json({
            'name': name,
            'host': host,
            'unmanaged_path': unmanaged_path,
            'group': group,
            'usage_mode': usage_mode,
            'permission': permission,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_by_id(cls, oid):
        rqst = Request(api_session.get(), 'DELETE', '/folders')
        rqst.set_json({'id': oid})
        async with rqst.fetch():
            return {}

    @api_function
    @classmethod
    async def list(cls, list_all=False):
        rqst = Request(api_session.get(), 'GET', '/folders')
        rqst.set_json({'all': list_all})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_hosts(cls):
        rqst = Request(api_session.get(), 'GET', '/folders/_/hosts')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_all_hosts(cls):
        rqst = Request(api_session.get(), 'GET', '/folders/_/all_hosts')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_allowed_types(cls):
        rqst = Request(api_session.get(), 'GET', '/folders/_/allowed_types')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def info(self):
        rqst = Request(api_session.get(), 'GET', '/folders/{0}'.format(self.name))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request(api_session.get(), 'DELETE', '/folders/{0}'.format(self.name))
        async with rqst.fetch():
            return {}

    @api_function
    async def rename(self, new_name):
        rqst = Request(api_session.get(), 'POST', '/folders/{0}/rename'.format(self.name))
        rqst.set_json({
            'new_name': new_name,
        })
        async with rqst.fetch() as resp:
            self.name = new_name
            return await resp.text()

    @api_function
    async def upload(self, files: Sequence[Union[str, Path]],
                     basedir: Union[str, Path] = None):

        base_file_path = (Path.cwd() if basedir is None
                          else Path(basedir).resolve())

        files = [Path(file).resolve() for file in files]
        total_size = 0
        for file_path in files:
            total_size += Path(file_path).stat().st_size

        session = api_session.get()
        config = session.config
        base_url = config.endpoint
        session_create_url = base_url / 'folders/{}/create_upload_session' \
                                        .format(self.name)
        session_upload_url = base_url / "folders/_/tus/upload/"

        for file_path in files:
            file_size = Path(file_path).stat().st_size
            params: Mapping = {'path': "{}".format(Path(file_path).name), 'size': int(file_size)}
            rqst = Request(api_session.get(),
                           'POST',
                           '/folders/{}/create_upload_session'
                           .format(self.name), params=params)

            rqst.content_type = "text/plain"
            date = datetime.now(tzutc())
            rqst.date = date
            rqst._sign(URL("/folders/{}/create_upload_session?path={}&size={}"
                       .format(self.name,
                               params['path'],
                               params['size'])))
            rqst.headers["Date"] = date.isoformat()
            rqst.headers["content-type"] = "text/plain"

            params = {'path': "{}".format(Path(file_path).name),
                      'size': int(file_size)}
            tus_client = client.TusClient(str(session_create_url),
                                          str(session_upload_url),
                                          rqst.headers, params)
            input_file = open(str(Path(file_path).relative_to(base_file_path)), "rb")
            print(file_path, base_file_path, str(Path(file_path).relative_to(base_file_path)))
            uploader = tus_client.async_uploader(file_stream=input_file)
            await uploader.upload()

    @api_function
    async def mkdir(self, path: Union[str, Path]):
        rqst = Request(api_session.get(), 'POST',
                       '/folders/{}/mkdir'.format(self.name))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    async def request_download(self, filename: Union[str, Path]):
        rqst = Request(api_session.get(), 'POST',
                       '/folders/{}/request_download'.format(self.name))
        rqst.set_json({
            'file': filename
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    async def rename_file(self, target_path: str, new_name: str):
        rqst = Request(api_session.get(), 'POST',
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
        rqst = Request(api_session.get(), 'DELETE',
                       '/folders/{}/delete_files'.format(self.name))
        rqst.set_json({
            'files': files,
            'recursive': recursive,
        })
        async with rqst.fetch() as resp:
            return await resp.text()

    @api_function
    async def download(self, files: Sequence[Union[str, Path]],
                       show_progress: bool = False):

        rqst = Request(api_session.get(), 'GET',
                       '/folders/{}/download'.format(self.name))
        rqst.set_json({
            'files': files,
        })
        file_names: List[str] = []
        async with rqst.fetch() as resp:
            if resp.status // 100 != 2:
                raise BackendAPIError(resp.status, resp.reason,
                                      await resp.text())
            total_bytes = int(resp.headers['X-TOTAL-PAYLOADS-LENGTH'])
            tqdm_obj = tqdm(desc='Downloading files',
                            unit='bytes', unit_scale=True,
                            total=total_bytes,
                            disable=not show_progress)
            reader = aiohttp.MultipartReader.from_response(resp.raw_response)
            with tqdm_obj as pbar:
                loop = current_loop()
                acc_bytes = 0
                while True:
                    part = cast(aiohttp.BodyPartReader, await reader.next())
                    if part is None:
                        break
                    assert part.headers.get(hdrs.CONTENT_ENCODING, 'identity').lower() in (
                        'identity',
                    )
                    assert part.headers.get(hdrs.CONTENT_TRANSFER_ENCODING, 'binary').lower() in (
                        'binary', '8bit', '7bit',
                    )
                    with open(part.filename, 'wb') as fp:
                        while True:
                            chunk = await part.read_chunk(DEFAULT_CHUNK_SIZE)
                            if not chunk:
                                break
                            await loop.run_in_executor(None, lambda: fp.write(chunk))
                            acc_bytes += len(chunk)
                            pbar.update(len(chunk))
                pbar.update(total_bytes - acc_bytes)
        return {'file_names': file_names}

    @api_function
    async def list_files(self, path: Union[str, Path] = '.'):
        rqst = Request(api_session.get(), 'GET', '/folders/{}/files'.format(self.name))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def invite(self, perm: str, emails: Sequence[str]):
        rqst = Request(api_session.get(), 'POST', '/folders/{}/invite'.format(self.name))
        rqst.set_json({
            'perm': perm, 'user_ids': emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def invitations(cls):
        rqst = Request(api_session.get(), 'GET', '/folders/invitations/list')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def accept_invitation(cls, inv_id: str):
        rqst = Request(api_session.get(), 'POST', '/folders/invitations/accept')
        rqst.set_json({'inv_id': inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_invitation(cls, inv_id: str):
        rqst = Request(api_session.get(), 'DELETE', '/folders/invitations/delete')
        rqst.set_json({'inv_id': inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_fstab_contents(cls, agent_id=None):
        rqst = Request(api_session.get(), 'GET', '/folders/_/fstab')
        rqst.set_json({
            'agent_id': agent_id,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def list_mounts(cls):
        rqst = Request(api_session.get(), 'GET', '/folders/_/mounts')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def mount_host(cls, name: str, fs_location: str, options=None,
                         edit_fstab: bool = False):
        rqst = Request(api_session.get(), 'POST', '/folders/_/mounts')
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
        rqst = Request(api_session.get(), 'DELETE', '/folders/_/mounts')
        rqst.set_json({
            'name': name,
            'edit_fstab': edit_fstab,
        })
        async with rqst.fetch() as resp:
            return await resp.json()
