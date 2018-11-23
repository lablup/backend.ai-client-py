import asyncio
from collections import OrderedDict, namedtuple
import contextlib
from datetime import datetime
import functools
import io
import sys
from typing import Any, Callable, Mapping, Union

import aiohttp
import aiohttp.web
import aiotools
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc
from multidict import CIMultiDict
import json

from .auth import generate_signature
from .exceptions import BackendClientError
from .session import BaseSession, Session as SyncSession, AsyncSession

__all__ = [
    'Request',
    'Response',
]


RequestContent = Union[
    bytes, bytearray, str,
    aiohttp.StreamReader,
    io.IOBase,
    None,
]


AttachedFile = namedtuple('AttachedFile', 'filename stream content_type')


class Request:
    '''
    The API request object.
    '''

    __slots__ = (
        'config', 'session', 'method', 'path',
        'date', 'headers', 'content_type',
        '_content', '_attached_files',
        'reporthook',
    )

    _allowed_methods = frozenset([
        'GET', 'HEAD', 'POST',
        'PUT', 'PATCH', 'DELETE',
        'OPTIONS'])

    def __init__(self, session: BaseSession,
                 method: str = 'GET',
                 path: str = None,
                 content: RequestContent = None, *,
                 content_type: str = None,
                 reporthook: Callable = None) -> None:
        '''
        Initialize an API request.

        :param Session session: The session object where this request is executed on.

        :param str path: The query path. When performing requests, the version number
                         prefix will be automatically perpended if required.

        :param Mapping content: The API query body which will be encoded as JSON.

        :param bool streaming: Make the response to be StreamingResponse.
        '''
        self.session = session
        self.config = session.config
        self.method = method
        if path.startswith('/'):
            path = path[1:]
        self.path = path
        self.date = None
        self.headers = CIMultiDict([
            ('User-Agent', self.config.user_agent),
            ('X-BackendAI-Version', self.config.version),
        ])
        self._attached_files = None
        self.set_content(content, content_type=content_type)
        self.reporthook = reporthook

    @property
    def content(self) -> Union[bytes, bytearray, None]:
        '''
        Retrieves the content in the original form.
        Private codes should NOT use this as it incurs duplicate
        encoding/decoding.
        '''
        return self._content

    def set_content(self, value: RequestContent, *,
                    content_type: str = None):
        '''
        Sets the content of the request.
        '''
        assert self._attached_files is None, \
               'cannot set content because you already attached files.'
        guessed_content_type = 'application/octet-stream'
        if value is None:
            guessed_content_type = 'text/plain'
            self._content = b''
        elif isinstance(value, str):
            guessed_content_type = 'text/plain'
            self._content = value.encode('utf-8')
        else:
            guessed_content_type = 'application/octet-stream'
            self._content = value
        self.content_type = (content_type if content_type is not None
                             else guessed_content_type)

    def set_json(self, value: object):
        self.set_content(json.dumps(value), content_type='application/json')

    def attach_files(self, files):
        assert not self._content, 'content must be empty to attach files.'
        self.content_type = 'multipart/form-data'
        for f in files:
            assert isinstance(f, AttachedFile)
        self._attached_files = files

    def _sign(self, access_key=None, secret_key=None, hash_type=None):
        '''
        Calculates the signature of the given request and adds the
        Authorization HTTP header.
        It should be called at the very end of request preparation and before
        sending the request to the server.
        '''
        if access_key is None:
            access_key = self.config.access_key
        if secret_key is None:
            secret_key = self.config.secret_key
        if hash_type is None:
            hash_type = self.config.hash_type
        if self.config.version >= 'v4.20181215':
            # new APIs don't use payload to calculate signatures
            payload = b''
        else:
            # assuming that the content object provides bytes serialization
            payload = bytes(self._content)
        hdrs, _ = generate_signature(
            self.method, self.config.version, self.config.endpoint,
            self.date, self.path, self.content_type, payload,
            access_key, secret_key, hash_type)
        self.headers.update(hdrs)

    def _pack_content(self):
        if self._attached_files is not None:
            data = aiohttp.FormData()
            for f in self._attached_files:
                data.add_field('src',
                               f.stream,
                               filename=f.filename,
                               content_type=f.content_type)
            assert data.is_multipart
            return data
        else:
            return self._content

    def build_url(self):
        base_url = self.config.endpoint.path.rstrip('/')
        query_path = self.path.lstrip('/') if len(self.path) > 0 else ''
        path = '{0}/{1}'.format(base_url, query_path)
        canonical_url = self.config.endpoint.with_path(path)
        return str(canonical_url)

    # TODO: attach rate-limit information

    def fetch(self, *args, **kwargs):
        '''
        Sends the request to the server.
        '''
        assert isinstance(self.session, SyncSession)
        execute = self.session.worker_thread.execute

        @contextlib.contextmanager
        def afetch_wrapper():
            afetch_ctx = self.afetch(*args, **kwargs)
            resp = execute(afetch_ctx.__aenter__())
            try:
                yield resp
            except:
                execute(afetch_ctx.__aexit__(*sys.exc_info()))
            else:
                execute(afetch_ctx.__aexit__(None, None, None))

        return afetch_wrapper(*args, **kwargs)

    @aiotools.actxmgr
    async def afetch(self, *, timeout=None):
        '''
        Sends the request to the server.

        This method is a coroutine.
        '''
        assert self.method in self._allowed_methods
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        if self.content_type is not None:
            self.headers['Content-Type'] = self.content_type
        try:
            self._sign()
            async with _timeout(timeout):
                client = self.session.aiohttp_session
                rqst_ctx = client.request(
                    self.method,
                    self.build_url(),
                    data=self._pack_content(),
                    headers=self.headers)
                async with rqst_ctx as raw_resp:
                    yield Response(self.session, raw_resp)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These exceptions must be bubbled up.
            raise
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e

    async def connect_websocket(self):
        '''
        Creates a WebSocket connection.

        This method is a coroutine.
        '''
        assert isinstance(self.session, AsyncSession)
        assert self.method == 'GET'
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        try:
            self._sign()
            client = self.session.aiohttp_session
            ws = await client.ws_connect(self.build_url(), headers=self.headers)
            return client, ws
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These exceptions must be bubbled up.
            raise
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e


class Response:
    '''
    Represents the Backend.AI API response.

    The response objects are meant to be created by the SDK, not the callers.

    text(), json() methods return the resolved content directly with plain
    synchronous Session while they return the coroutines with AsyncSession.
    '''

    __slots__ = (
        '_session', '_raw_response',
    )

    def __init__(self, session: BaseSession,
                 underlying_response: aiohttp.ClientResponse):
        self._session = session
        self._raw_response = underlying_response

    @property
    def session(self) -> BaseSession:
        return self._session

    @property
    def status(self) -> int:
        return self._raw_response.status

    @property
    def reason(self) -> str:
        return self._raw_response.reason

    @property
    def headers(self) -> Mapping[str, str]:
        return self._raw_response.headers

    @property
    def raw_response(self) -> aiohttp.ClientResponse:
        return self._raw_response

    @property
    def content_type(self):
        return self._raw_response.content_type

    @property
    def content_length(self):
        return self._raw_response.content_length

    @property
    def content(self) -> aiohttp.StreamReader:
        return self._raw_response.content

    def text(self) -> str:
        if isinstance(self._session, SyncSession):
            return self._session.worker_thread.execute(self._raw_response.text())
        else:
            return self._raw_response.text()

    def json(self, loads=json.loads) -> Any:
        loads = functools.partial(loads, object_pairs_hook=OrderedDict)
        if isinstance(self._session, SyncSession):
            return loads(self.text())
        else:
            return self._raw_response.json(loads=loads)

    def read(self, n=-1) -> bytes:
        return self._session.worker_thread.execute(self.aread(n))

    async def aread(self, n=-1) -> bytes:
        return await self._raw_response.content.read(n)

    def readall(self) -> bytes:
        return self._session.worker_thread.execute(self._areadall())

    async def areadall(self) -> bytes:
        return await self._raw_response.content.read(-1)
