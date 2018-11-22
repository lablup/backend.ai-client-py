import asyncio
from collections import OrderedDict
import contextlib
from datetime import datetime
import io
import sys
from typing import Any, Callable, Mapping, Sequence, Union

import aiohttp
import aiohttp.web
import aiotools
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc
from multidict import CIMultiDict
import json

from .auth import generate_signature
from .config import APIConfig
from .exceptions import BackendClientError
from .session import BaseSession, Session as SyncSession, AsyncSession

__all__ = [
    'Request',
    'Response',
]


class BaseRequest:

    __slots__ = ['config', 'session', 'method', 'path',
                 'date', 'headers',
                 'streaming',
                 'content_type', '_content']

    _allowed_methods = frozenset([
        'GET', 'HEAD', 'POST',
        'PUT', 'PATCH', 'DELETE',
        'OPTIONS'])

    def __init__(self, session: BaseSession,
                 method: str = 'GET',
                 path: str = None,
                 content: Mapping = None, *,
                 content_type: str = None,
                 streaming: bool = False,
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
        self.streaming = streaming
        self.method = method
        if path.startswith('/'):
            path = path[1:]
        self.path = path
        self.date = None
        self.headers = CIMultiDict([
            ('User-Agent', self.config.user_agent),
            ('X-BackendAI-Version', self.config.version),
        ])
        self.content_type = content_type
        self.content = content if content is not None else b''
        self.reporthook = reporthook

    @property
    def content(self) -> Union[bytes, bytearray, None]:
        '''
        Retrieves the content in the original form.
        Private codes should NOT use this as it incurs duplicate
        encoding/decoding.
        '''
        return self._content

    @content.setter
    def content(self, value: Union[bytes, bytearray,
                                   Mapping[str, Any],
                                   Sequence[Any],
                                   aiohttp.StreamReader,
                                   io.IOBase]):
        '''
        Sets the content of the request.
        Depending on the type of content, it automatically sets appropriate
        headers such as content-type and content-length.
        '''
        self._content = value

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

    def build_url(self):
        base_url = self.config.endpoint.path.rstrip('/')
        major_ver = self.config.version.split('.', 1)[0]
        query_path = self.path.lstrip('/') if len(self.path) > 0 else ''
        path = '{0}/{1}/{2}'.format(base_url, major_ver, query_path)
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
            afetch_ctx = execute(self.afetch(*args, **kwargs))
            resp = execute(afetch_ctx.__aenter__())
            try:
                yield resp
            except:
                execute(afetch_ctx.__aexit__(*sys.exc_info))
            else:
                execute(afetch_ctx.__aexit__(None, None, None))

        return self.afetch_wrapper(*args, **kwargs)

    @aiotools.actxmgr
    async def afetch(self, *, timeout=None):
        '''
        Sends the request to the server.

        This method is a coroutine.
        '''
        assert self.method in self._allowed_methods
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        self.headers['Content-Type'] = self.content_type
        try:
            self._sign()
            async with _timeout(timeout):
                client = self.session.aiohttp_session
                rqst_ctx = client.request(
                    self.method,
                    self.build_url(),
                    data=self.pack_content(),
                    headers=self.headers)
                async with rqst_ctx as resp:
                    yield resp
                    #if self.streaming:
                    #    return StreamingResponse(
                    #        self.session,
                    #        resp,
                    #        stream=resp.content,
                    #        content_type=resp.content_type)
                    #else:
                    #    body = await resp.read()
                    #    return Response(
                    #        self.session,
                    #        resp,
                    #        body=body,
                    #        content_type=resp.content_type,
                    #        charset=resp.charset)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These exceptions must be bubbled up.
            raise
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e

    def pack_content(self):
        if self.content_type == 'multipart/form-data':
            data = aiohttp.FormData()
            for f in self._content:
                data.add_field(f.name,
                               f.file,
                               filename=f.filename,
                               content_type=f.content_type)
            assert data.is_multipart
            return data
        else:
            return self._content

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


class Request(BaseRequest):
    pass


class StreamingRequest(Request):
    __slots__ = ('config', 'method', 'path',
                 'date', 'headers',
                 'content_type', '_content', 'reporthook')

    def __init__(self, session: AsyncSession,
                 method: str = 'GET',
                 path: str = None,
                 content: Mapping = None,
                 **kwargs) -> None:
        super().__init__(session, method, path, content, **kwargs)

    @property
    def content(self) -> Union[aiohttp.StreamReader, bytes, bytearray, None]:
        if isinstance(self.content, aiohttp.StreamReader):
            return self._content
        return Request.content.fget(self)

    @content.setter
    def content(self, value: Union[aiohttp.StreamReader,
                                   bytes, bytearray,
                                   Mapping[str, Any],
                                   Sequence[Any],
                                   None]):

        if isinstance(value, aiohttp.StreamReader):
            self._content = value
        else:
            Request.content.fset(self, value)

    #def pack_content(self):
    #    if isinstance(self.content, aiohttp.StreamReader):
    #        return self._content
    #    super().pack_content()


class BaseResponse:
    __slots__ = (
        '_response', '_session',
    )

    def __init__(self, session: BaseSession,
                 underlying_response: aiohttp.ClientResponse):
        self._session = session
        self._response = underlying_response

    @property
    def status(self) -> int:
        return self._response.status

    @property
    def reason(self) -> str:
        return self._response.reason

    @property
    def headers(self) -> Mapping[str, str]:
        return self._response.headers

    @property
    def raw_response(self) -> aiohttp.ClientResponse:
        return self._response

    @property
    def session(self) -> BaseSession:
        return self._session


class Response(BaseResponse):

    __slots__ = BaseResponse.__slots__ + (
        '_body', '_content_type', '_content_length', '_charset',
    )

    def __init__(self, session: BaseSession,
                 underlying_response: aiohttp.ClientResponse, *,
                 body: Union[bytes, bytearray] = b'',
                 content_type: str = 'text/plain',
                 content_length: int = None,
                 charset: str = None):
        super().__init__(session, underlying_response)
        self._body = body
        self._content_type = content_type
        self._content_length = content_length
        self._charset = charset if charset else 'utf-8'

    @property
    def content_type(self):
        return self._content_type

    @property
    def content_length(self):
        is_multipart = self._content_type.startswith('multipart/')
        if self._content_length is None and not is_multipart and self._body:
            return len(self._body)
        return self._content_length

    @property
    def charset(self):
        return self._charset

    @property
    def content(self) -> bytes:
        return self._body

    def text(self) -> str:
        return self._body.decode(self._charset)

    def json(self, loads=json.loads):
        return loads(self.text(), object_pairs_hook=OrderedDict)


class StreamingResponse(BaseResponse):

    __slots__ = BaseResponse.__slots__ + (
        '_stream', '_content_type',
    )

    def __init__(self, session: BaseSession,
                 underlying_response: aiohttp.ClientResponse, *,
                 stream: aiohttp.streams.StreamReader = None,
                 content_type: str = 'text/plain'):
        super().__init__(session, underlying_response)
        self._stream = stream
        self._content_type = content_type

    @property
    def content_type(self):
        return self._content_type

    @property
    def stream(self) -> aiohttp.streams.StreamReader:
        return self._stream

    def read(self, n=-1) -> bytes:
        return self._session.worker_thread.execute(self.aread(n))

    async def aread(self, n=-1) -> bytes:
        if self._stream.at_eof:
            return b''
        return await self._stream.read(n)

    def readall(self) -> bytes:
        return self._session.worker_thread.execute(self._areadall())

    async def areadall(self) -> bytes:
        return await self._stream.read(-1)
