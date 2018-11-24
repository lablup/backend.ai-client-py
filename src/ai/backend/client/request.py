import asyncio
from collections import OrderedDict, namedtuple
from datetime import datetime
import functools
import io
from typing import Any, Callable, Mapping, Sequence, Union

import aiohttp
import aiohttp.web
from dateutil.tz import tzutc
from multidict import CIMultiDict
import json as modjson

from .auth import generate_signature
from .exceptions import BackendClientError, BackendAPIError
from .session import BaseSession, Session as SyncSession, AsyncSession

__all__ = [
    'Request',
    'Response',
]


'''
The type alias for the set of allowed types for request content.
'''
RequestContent = Union[
    bytes, bytearray, str,
    aiohttp.StreamReader,
    io.IOBase,
    None,
]


'''
A struct that represents an attached file to the API request.

:param str filename: The name of file to store. It may include paths
                     and the server will create parent directories
                     if required.

:param Any stream: A file-like object that allows stream-reading bytes.

:param str content_type: The content type for the stream.  For arbitrary
                         binary data, use "application/octet-stream".
'''
AttachedFile = namedtuple('AttachedFile', 'filename stream content_type')


class FetchContextManager:
    '''
    The wrapper for :func:`Request.fetch` for both sync/async sessions.
    '''

    __slots__ = ('session', 'rqst_ctx', 'async_mode')

    def __init__(self, session, rqst_ctx):
        self.session = session
        self.rqst_ctx = rqst_ctx
        self.async_mode = True

    def __enter__(self):
        assert isinstance(self.session, SyncSession)
        self.async_mode = False
        return self.session.worker_thread.execute(self.__aenter__())

    async def __aenter__(self):
        try:
            raw_resp = await self.rqst_ctx.__aenter__()
            if raw_resp.status // 100 != 2:
                msg = await raw_resp.text()
                raise BackendAPIError(raw_resp.status, raw_resp.reason, msg)
            return Response(self.session, raw_resp, async_mode=self.async_mode)
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e

    def __exit__(self, *args):
        return self.session.worker_thread.execute(self.__aexit__(*args))

    async def __aexit__(self, *args):
        return await self.rqst_ctx.__aexit__(*args)


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

        :param BaseSession session: The session where this request is executed on.

        :param str path: The query path. When performing requests, the version number
                         prefix will be automatically perpended if required.

        :param RequestContent content: The API query body which will be encoded as
                                       JSON.

        :param str content_type: Explicitly set the content type.  See also
                                 :func:`Request.set_content`.
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
    def content(self) -> RequestContent:
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
        '''
        A shortcut for set_content() with JSON objects.
        '''
        self.set_content(modjson.dumps(value), content_type='application/json')

    def attach_files(self, files: Sequence[AttachedFile]):
        '''
        Attach a list of files represented as AttachedFile.
        '''
        assert not self._content, 'content must be empty to attach files.'
        self.content_type = 'multipart/form-data'
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
        hdrs, _ = generate_signature(
            self.method, self.config.version, self.config.endpoint,
            self.date, self.path, self.content_type, self._content,
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
            # Let aiohttp fill up the content-type header including
            # multipart boundaries.
            self.headers.pop('Content-Type')
            return data
        else:
            return self._content

    def _build_url(self):
        base_url = self.config.endpoint.path.rstrip('/')
        query_path = self.path.lstrip('/') if len(self.path) > 0 else ''
        path = '{0}/{1}'.format(base_url, query_path)
        canonical_url = self.config.endpoint.with_path(path)
        return str(canonical_url)

    # TODO: attach rate-limit information

    def fetch(self, *args, **kwargs):
        '''
        Sends the request to the server.

        You may use this method either with plain synchronous Session or
        AsyncSession.
        '''
        assert self.method in self._allowed_methods
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        if self.content_type is not None:
            self.headers['Content-Type'] = self.content_type
        self._sign()
        rqst_ctx = self.session.aiohttp_session.request(
            self.method,
            self._build_url(),
            data=self._pack_content(),
            headers=self.headers)
        return FetchContextManager(self.session, rqst_ctx)

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
            ws = await client.ws_connect(self._build_url(), headers=self.headers)
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

    :func:`text`, :func:`json` methods return the resolved content directly with
    plain synchronous Session while they return the coroutines with AsyncSession.
    '''

    __slots__ = (
        '_session', '_raw_response', '_async_mode',
    )

    def __init__(self, session: BaseSession,
                 underlying_response: aiohttp.ClientResponse, *,
                 async_mode: bool = False):
        self._session = session
        self._raw_response = underlying_response
        self._async_mode = async_mode

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
    def content_type(self) -> str:
        return self._raw_response.content_type

    @property
    def content_length(self) -> int:
        return self._raw_response.content_length

    @property
    def content(self) -> aiohttp.StreamReader:
        return self._raw_response.content

    def text(self) -> str:
        if self._async_mode:
            return self._raw_response.text()
        else:
            return self._session.worker_thread.execute(self._raw_response.text())

    def json(self, *, loads=modjson.loads) -> Any:
        loads = functools.partial(loads, object_pairs_hook=OrderedDict)
        if self._async_mode:
            return self._raw_response.json(loads=loads)
        else:
            return self._session.worker_thread.execute(
                self._raw_response.json(loads=loads))

    def read(self, n=-1) -> bytes:
        return self._session.worker_thread.execute(self.aread(n))

    async def aread(self, n=-1) -> bytes:
        return await self._raw_response.content.read(n)

    def readall(self) -> bytes:
        return self._session.worker_thread.execute(self._areadall())

    async def areadall(self) -> bytes:
        return await self._raw_response.content.read(-1)
