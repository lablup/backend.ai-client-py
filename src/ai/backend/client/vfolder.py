import asyncio
from datetime import datetime
from pathlib import Path
import re
from typing import Sequence, Union
import zlib

import aiohttp
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc
from tqdm import tqdm

from .base import BaseFunction, SyncFunctionMixin
from .exceptions import BackendAPIError, BackendClientError
from .request import Request
from .cli.pretty import ProgressReportingReader

__all__ = (
    'BaseVFolder',
    'VFolder',
)

_rx_slug = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$')


class BaseVFolder(BaseFunction):

    _session = None

    @classmethod
    def _create(cls, name: str, host: str=None):
        assert _rx_slug.search(name) is not None
        resp = yield Request(cls._session, 'POST', '/folders/', {
            'name': name,
            'host': host,
        })
        return resp.json()

    @classmethod
    def _list(cls):
        resp = yield Request(cls._session, 'GET', '/folders/')
        return resp.json()

    @classmethod
    def _get(cls, name: str):
        return cls(name)

    def _info(self):
        resp = yield Request(self._session,
                             'GET', '/folders/{0}'.format(self.name))
        return resp.json()

    def _delete(self):
        resp = yield Request(self._session,
                             'DELETE', '/folders/{0}'.format(self.name))
        if resp.status == 200:
            return resp.json()

    def _upload(self, files: Sequence[Union[str, Path]],
               basedir: Union[str, Path]=None,
               show_progress: bool=False):
        fields = []
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
            for file_path in files:
                try:
                    fields.append(aiohttp.web.FileField(
                        'src',
                        str(file_path.relative_to(base_path)),
                        ProgressReportingReader(str(file_path),
                                                tqdm_instance=tqdm_obj),
                        'application/octet-stream',
                        None
                    ))
                except ValueError:
                    msg = 'File "{0}" is outside of the base directory "{1}".' \
                          .format(file_path, base_path)
                    raise ValueError(msg) from None

            rqst = Request(self._session,
                           'POST', '/folders/{}/upload'.format(self.name))
            rqst.content = fields
            resp = yield rqst
        return resp

    def _mkdir(self,
                      path: Union[str, Path]):
        resp = yield Request(
            self._session,
            'POST', '/folders/{}/mkdir'.format(self.name),
            {
                'path': path,
            })
        return resp

    def _delete_files(self,
                      files: Sequence[Union[str, Path]],
                      recursive: bool=False):
        resp = yield Request(
            self._session,
            'DELETE', '/folders/{}/delete_files'.format(self.name),
            {
                'files': files,
                'recursive': recursive,
            })
        return resp

    def _download(self, files: Sequence[Union[str, Path]],
                  show_progress: bool=False):

        async def _stream_download():
            rqst = Request(self._session,
                'GET', '/folders/{}/download'.format(self.name), {
                    'files': files,
                })
            rqst.date = datetime.now(tzutc())
            rqst.headers['Date'] = rqst.date.isoformat()
            try:
                client = self._session.aiohttp_session
                rqst._sign()
                async with _timeout(None):
                    rqst_ctx = client.request(rqst.method,
                                              rqst.build_url(),
                                              data=rqst.pack_content(),
                                              headers=rqst.headers)
                    async with rqst_ctx as resp:
                        if resp.status // 100 != 2:
                            raise BackendAPIError(resp.status, resp.reason,
                                                  await resp.text())
                        total_bytes = int(resp.headers['X-TOTAL-PAYLOADS-LENGTH'])
                        tqdm_obj = tqdm(desc='Downloading files',
                                        unit='bytes', unit_scale=True,
                                        total=total_bytes,
                                        disable=not show_progress)
                        reader = aiohttp.MultipartReader.from_response(resp)
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

        self._session.worker_thread.execute(_stream_download())

    def _list_files(self, path: Union[str, Path]='.'):
        resp = yield Request(self._session,
            'GET', '/folders/{}/files'.format(self.name), {
                'path': path,
            })
        return resp.json()

    def _invite(self, perm: str, emails: Sequence[str]):
        resp = yield Request(self._session,
            'POST', '/folders/{}/invite'.format(self.name), {
                'perm': perm, 'user_ids': emails,
            })
        return resp.json()

    @classmethod
    def _invitations(cls):
        resp = yield Request(cls._session, 'GET', '/folders/invitations/list')
        return resp.json()

    @classmethod
    def _accept_invitation(cls, inv_id: str, inv_ak: str):
        resp = yield Request(cls._session, 'POST', '/folders/invitations/accept',
                             {'inv_id': inv_id, 'inv_ak': inv_ak})
        return resp.json()

    @classmethod
    def _delete_invitation(cls, inv_id: str):
        resp = yield Request(cls._session, 'DELETE', '/folders/invitations/delete',
                             {'inv_id': inv_id})
        return resp.json()

    def __init__(self, name: str):
        assert _rx_slug.search(name) is not None
        self.name = name
        self.delete   = self._call_base_method(self._delete)
        self.info     = self._call_base_method(self._info)
        self.upload   = self._call_base_method(self._upload)
        # self.download = self._call_base_method(self._download)
        # To deliver loop and session objects to Request.send method.
        # TODO: Generalized request/response abstraction accounting for streaming
        #       would be needed.
        self.download = self._download
        self.mkdir = self._call_base_method(self._mkdir)
        self.delete_files = self._call_base_method(self._delete_files)
        self.list_files = self._call_base_method(self._list_files)
        self.invite = self._call_base_method(self._invite)

    def __init_subclass__(cls):
        cls.create = cls._call_base_clsmethod(cls._create)
        cls.list   = cls._call_base_clsmethod(cls._list)
        cls.get    = cls._call_base_clsmethod(cls._get)
        cls.invitations = cls._call_base_clsmethod(cls._invitations)
        cls.accept_invitation = cls._call_base_clsmethod(cls._accept_invitation)
        cls.delete_invitation = cls._call_base_clsmethod(cls._delete_invitation)


class VFolder(SyncFunctionMixin, BaseVFolder):
    '''
    Deprecated! Use ai.backend.client.Session instead.
    '''
    pass
