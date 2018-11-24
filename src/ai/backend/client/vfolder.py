import asyncio
from pathlib import Path
import re
from typing import Sequence, Union
import zlib

import aiohttp
from tqdm import tqdm

from .base import api_function
from .exceptions import BackendAPIError, BackendClientError
from .request import Request, AttachedFile
from .cli.pretty import ProgressReportingReader

__all__ = (
    'VFolder',
)

_rx_slug = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$')


class VFolder:

    session = None

    @api_function
    @classmethod
    async def create(cls, name: str):
        assert _rx_slug.search(name) is not None
        rqst = Request(cls.session, 'POST', '/folders')
        rqst.set_json({
            'name': name,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    def __init__(self, name: str):
        assert _rx_slug.search(name) is not None, 'Invalid vfolder name format'
        self.name = name

    @api_function
    @classmethod
    async def list(cls):
        rqst = Request(cls.session, 'GET', '/folders')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def info(self):
        rqst = Request(self.session, 'GET', '/folders/{0}'.format(self.name))
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request(self.session, 'DELETE', '/folders/{0}'.format(self.name))
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.json()

    @api_function
    async def upload(self, files: Sequence[Union[str, Path]],
                     basedir: Union[str, Path] = None,
                     show_progress: bool = False):
        base_path = (Path.cwd() if basedir is None
                     else Path(basedir).resolve())
        files = [Path(file).resolve() for file in files]
        total_size = 0
        for file_path in files:
            total_size += file_path.stat().st_size
        tqdm_obj = tqdm(desc='Uploading files',
                        unit='bytes', unit_scale=True,
                        total=total_size,
                        disable=not show_progress)
        with tqdm_obj:
            attachments = []
            for file_path in files:
                try:
                    attachments.append(AttachedFile(
                        str(file_path.relative_to(base_path)),
                        ProgressReportingReader(str(file_path),
                                                tqdm_instance=tqdm_obj),
                        'application/octet-stream',
                    ))
                except ValueError:
                    msg = 'File "{0}" is outside of the base directory "{1}".' \
                          .format(file_path, base_path)
                    raise ValueError(msg) from None

            rqst = Request(self.session,
                           'POST', '/folders/{}/upload'.format(self.name))
            rqst.attach_files(attachments)
            async with rqst.fetch() as resp:
                return resp

    @api_function
    async def mkdir(self, path: Union[str, Path]):
        rqst = Request(self.session, 'POST',
                       '/folders/{}/mkdir'.format(self.name))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return resp

    @api_function
    async def delete_files(self,
                            files: Sequence[Union[str, Path]],
                            recursive: bool = False):
        rqst = Request(self.session, 'DELETE',
                       '/folders/{}/delete_files'.format(self.name))
        rqst.set_json({
            'files': files,
            'recursive': recursive,
        })
        async with rqst.fetch() as resp:
            return resp

    @api_function
    async def download(self, files: Sequence[Union[str, Path]],
                        show_progress: bool = False):

        rqst = Request(self.session, 'GET',
                       '/folders/{}/download'.format(self.name))
        rqst.set_json({
            'files': files,
        })
        try:
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
                    acc_bytes = 0
                    while True:
                        part = await reader.next()
                        if part is None:
                            break
                        # It seems like that there's no automatic
                        # decompression steps in multipart reader for
                        # chuncked encoding.
                        encoding = part.headers['Content-Encoding']
                        zlib_mode = (16 + zlib.MAX_WBITS
                                         if encoding == 'gzip'
                                         else -zlib.MAX_WBITS)
                        decompressor = zlib.decompressobj(wbits=zlib_mode)
                        fp = open(part.filename, 'wb')
                        while True:
                            # default chunk size: 8192
                            chunk = await part.read_chunk()
                            if not chunk:
                                break
                            raw_chunk = decompressor.decompress(chunk)
                            fp.write(raw_chunk)
                            acc_bytes += len(raw_chunk)
                            pbar.update(len(raw_chunk))
                        fp.close()
                    pbar.update(total_bytes - acc_bytes)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These exceptions must be bubbled up.
            raise
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e

    @api_function
    async def list_files(self, path: Union[str, Path] = '.'):
        rqst = Request(self.session, 'GET', '/folders/{}/files'.format(self.name))
        rqst.set_json({
            'path': path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def invite(self, perm: str, emails: Sequence[str]):
        rqst = Request(self.session, 'POST', '/folders/{}/invite'.format(self.name))
        rqst.set_json({
            'perm': perm, 'user_ids': emails,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def invitations(cls):
        rqst = Request(cls.session, 'GET', '/folders/invitations/list')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def accept_invitation(cls, inv_id: str, inv_ak: str):
        rqst = Request(cls.session, 'POST', '/folders/invitations/accept')
        rqst.set_json({'inv_id': inv_id, 'inv_ak': inv_ak})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def delete_invitation(cls, inv_id: str):
        rqst = Request(cls.session, 'DELETE', '/folders/invitations/delete')
        rqst.set_json({'inv_id': inv_id})
        async with rqst.fetch() as resp:
            return await resp.json()
