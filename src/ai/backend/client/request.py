from collections import OrderedDict, namedtuple
from datetime import datetime
from decimal import Decimal
import functools
import io
import logging
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence, Union

import aiohttp
from aiohttp.client import _RequestContextManager, _WSRequestContextManager
import aiohttp.web
import appdirs
from dateutil.tz import tzutc
from multidict import CIMultiDict
import json as modjson

from .auth import generate_signature
from .exceptions import BackendClientError, BackendAPIError
from .session import BaseSession, Session as SyncSession, AsyncSession

log = logging.getLogger('ai.backend.client.request')

__all__ = [
    'Request',
    'Response',
    'WebSocketResponse',
    'SSEResponse',
    'AttachedFile',
]


RequestContent = Union[
    bytes, bytearray, str,
    aiohttp.StreamReader,
    io.IOBase,
    None,
]
'''
The type alias for the set of allowed types for request content.
'''


AttachedFile = namedtuple('AttachedFile', 'filename stream content_type')
'''
A struct that represents an attached file to the API request.

:param str filename: The name of file to store. It may include paths
                     and the server will create parent directories
                     if required.

:param Any stream: A file-like object that allows stream-reading bytes.

:param str content_type: The content type for the stream.  For arbitrary
                         binary data, use "application/octet-stream".
'''


class ExtendedJSONEncoder(modjson.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Request:
    '''
    The API request object.
    '''

    __slots__ = (
        'config', 'session', 'method', 'path',
        'date', 'headers', 'params', 'content_type',
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
                 params: Mapping[str, str] = None,
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
        self.params = params
        self.date = None
        self.headers = CIMultiDict([
            ('User-Agent', self.config.user_agent),
            ('X-BackendAI-Domain', self.config.domain),
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
        self.set_content(modjson.dumps(value, cls=ExtendedJSONEncoder),
                         content_type='application/json')

    def attach_files(self, files: Sequence[AttachedFile]):
        '''
        Attach a list of files represented as AttachedFile.
        '''
        assert not self._content, 'content must be empty to attach files.'
        self.content_type = 'multipart/form-data'
        self._attached_files = files

    def _sign(self, rel_url, access_key=None, secret_key=None, hash_type=None):
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
        if self.config.endpoint_type == 'api':
            hdrs, _ = generate_signature(
                self.method, self.config.version, self.config.endpoint,
                self.date, str(rel_url), self.content_type, self._content,
                access_key, secret_key, hash_type)
            self.headers.update(hdrs)
        elif self.config.endpoint_type == 'session':
            local_state_path = Path(appdirs.user_state_dir('backend.ai', 'Lablup'))
            try:
                self.session.aiohttp_session.cookie_jar.load(
                    local_state_path / 'cookie.dat')
            except (IOError, PermissionError):
                pass
        else:
            raise ValueError('unsupported endpoint type')

    def _pack_content(self):
        if self._attached_files is not None:
            data = aiohttp.FormData()
            for f in self._attached_files:
                data.add_field('src',
                               f.stream,
                               filename=f.filename,
                               content_type=f.content_type)
            assert data.is_multipart, 'Failed to pack files as multipart.'
            # Let aiohttp fill up the content-type header including
            # multipart boundaries.
            self.headers.pop('Content-Type', None)
            return data
        else:
            return self._content

    def _build_url(self):
        base_url = self.config.endpoint.path.rstrip('/')
        query_path = self.path.lstrip('/') if len(self.path) > 0 else ''
        if self.config.endpoint_type == 'session':
            if not query_path.startswith('server'):
                query_path = 'func/{0}'.format(query_path)
        path = '{0}/{1}'.format(base_url, query_path)
        url = self.config.endpoint.with_path(path)
        if self.params:
            url = url.with_query(self.params)
        return url

    # TODO: attach rate-limit information

    def fetch(self, **kwargs) -> 'FetchContextManager':
        '''
        Sends the request to the server and reads the response.

        You may use this method either with plain synchronous Session or
        AsyncSession.  Both the followings patterns are valid:

        .. code-block:: python3

          from ai.backend.client.request import Request
          from ai.backend.client.session import Session

          with Session() as sess:
            rqst = Request(sess, 'GET', ...)
            with rqst.fetch() as resp:
              print(resp.text())

        .. code-block:: python3

          from ai.backend.client.request import Request
          from ai.backend.client.session import AsyncSession

          async with AsyncSession() as sess:
            rqst = Request(sess, 'GET', ...)
            async with rqst.fetch() as resp:
              print(await resp.text())
        '''
        assert self.method in self._allowed_methods, \
               'Disallowed HTTP method: {}'.format(self.method)
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        if self.content_type is not None and 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = self.content_type
        force_anonymous = kwargs.pop('anonymous', False)

        def _rqst_ctx_builder():
            timeout_config = aiohttp.ClientTimeout(
                total=None, connect=None,
                sock_connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout,
            )
            full_url = self._build_url()
            if not self.config.is_anonymous and not force_anonymous:
                self._sign(full_url.relative())
            return self.session.aiohttp_session.request(
                self.method,
                str(full_url),
                data=self._pack_content(),
                timeout=timeout_config,
                headers=self.headers)

        return FetchContextManager(self.session, _rqst_ctx_builder, **kwargs)

    def connect_websocket(self, **kwargs) -> 'WebSocketContextManager':
        '''
        Creates a WebSocket connection.

        .. warning::

          This method only works with
          :class:`~ai.backend.client.session.AsyncSession`.
        '''
        assert isinstance(self.session, AsyncSession), \
               'Cannot use websockets with sessions in the synchronous mode'
        assert self.method == 'GET', 'Invalid websocket method'
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        # websocket is always a "binary" stream.
        self.content_type = 'application/octet-stream'

        def _ws_ctx_builder():
            full_url = self._build_url()
            if not self.config.is_anonymous:
                self._sign(full_url.relative())
            return self.session.aiohttp_session.ws_connect(
                str(full_url),
                autoping=True, heartbeat=30.0,
                headers=self.headers)

        return WebSocketContextManager(self.session, _ws_ctx_builder, **kwargs)

    def connect_events(self, **kwargs) -> 'SSEContextManager':
        '''
        Creates a Server-Sent Events connection.

        .. warning::

          This method only works with
          :class:`~ai.backend.client.session.AsyncSession`.
        '''
        assert isinstance(self.session, AsyncSession), \
               'Cannot use event streams with sessions in the synchronous mode'
        assert self.method == 'GET', 'Invalid event stream method'
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        self.content_type = 'application/octet-stream'

        def _rqst_ctx_builder():
            timeout_config = aiohttp.ClientTimeout(
                total=None, connect=None,
                sock_connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout,
            )
            full_url = self._build_url()
            if not self.config.is_anonymous:
                self._sign(full_url.relative())
            return self.session.aiohttp_session.request(
                self.method,
                str(full_url),
                timeout=timeout_config,
                headers=self.headers)

        return SSEContextManager(self.session, _rqst_ctx_builder, **kwargs)


class Response:
    '''
    Represents the Backend.AI API response.
    Also serves as a high-level wrapper of :class:`aiohttp.ClientResponse`.

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


class FetchContextManager:
    '''
    The context manager returned by :func:`Request.fetch`.

    It provides both synchronouse and asynchronous contex manager interfaces.
    '''

    __slots__ = (
        'session', 'rqst_ctx_builder', 'response_cls',
        'check_status',
        '_async_mode',
        '_rqst_ctx',
    )

    def __init__(self, session: BaseSession,
                 rqst_ctx_builder: Callable[[], _RequestContextManager], *,
                 response_cls: Response = Response,
                 check_status: bool = True):
        self.session = session
        self.rqst_ctx_builder = rqst_ctx_builder
        self.response_cls = response_cls
        self.check_status = check_status
        self._async_mode = True
        self._rqst_ctx = None

    def __enter__(self):
        assert isinstance(self.session, SyncSession)
        self._async_mode = False
        return self.session.worker_thread.execute(self.__aenter__())

    async def __aenter__(self):
        max_retries = len(self.session.config.endpoints)
        retry_count = 0
        while True:
            try:
                retry_count += 1
                self._rqst_ctx = self.rqst_ctx_builder()
                raw_resp = await self._rqst_ctx.__aenter__()
                if self.check_status and raw_resp.status // 100 != 2:
                    msg = await raw_resp.text()
                    await raw_resp.__aexit__(None, None, None)
                    raise BackendAPIError(raw_resp.status, raw_resp.reason, msg)
                return self.response_cls(self.session, raw_resp,
                                         async_mode=self._async_mode)
            except aiohttp.ClientConnectionError as e:
                if retry_count == max_retries:
                    msg = 'Request to the API endpoint has failed.\n' \
                          'Check your network connection and/or the server status.\n' \
                          '\u279c {!r}'.format(e)
                    raise BackendClientError(msg) from e
                else:
                    self.session.config.rotate_endpoints()
                    continue
            except aiohttp.ClientResponseError as e:
                msg = 'API endpoint response error.\n' \
                      '\u279c {!r}'.format(e)
                await raw_resp.__aexit__(*sys.exc_info())
                raise BackendClientError(msg) from e

    def __exit__(self, *args):
        return self.session.worker_thread.execute(self.__aexit__(*args))

    async def __aexit__(self, *args):
        ret = await self._rqst_ctx.__aexit__(*args)
        self._rqst_ctx = None
        return ret


class WebSocketResponse:
    '''
    A high-level wrapper of :class:`aiohttp.ClientWebSocketResponse`.
    '''

    __slots__ = ('_session', '_raw_ws', )

    def __init__(self, session: BaseSession,
                 underlying_ws: aiohttp.ClientWebSocketResponse):
        self._session = session
        self._raw_ws = underlying_ws

    @property
    def session(self) -> BaseSession:
        return self._session

    @property
    def raw_weboscket(self) -> aiohttp.ClientWebSocketResponse:
        return self._raw_ws

    @property
    def closed(self):
        return self._raw_ws.closed

    async def close(self):
        await self._raw_ws.close()

    def __aiter__(self):
        return self._raw_ws.__aiter__()

    async def __anext__(self):
        return await self._raw_ws.__anext__()

    def exception(self):
        return self._raw_ws.exception()

    async def send_str(self, raw_str: str):
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError('server disconnected')
        await self._raw_ws.send_str(raw_str)

    async def send_json(self, obj: Any):
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError('server disconnected')
        await self._raw_ws.send_json(obj)

    async def send_bytes(self, data: bytes):
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError('server disconnected')
        await self._raw_ws.send_bytes(data)

    async def receive_str(self) -> str:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError('server disconnected')
        return await self._raw_ws.receive_str()

    async def receive_json(self) -> Any:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError('server disconnected')
        return await self._raw_ws.receive_json()

    async def receive_bytes(self) -> bytes:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError('server disconnected')
        return await self._raw_ws.receive_bytes()


class WebSocketContextManager:
    '''
    The context manager returned by :func:`Request.connect_websocket`.
    '''

    __slots__ = (
        'session', 'ws_ctx_builder', 'response_cls',
        'on_enter',
        '_ws_ctx',
    )

    def __init__(self, session: BaseSession,
                 ws_ctx_builder: Callable[[], _WSRequestContextManager], *,
                 on_enter: Callable = None,
                 response_cls: WebSocketResponse = WebSocketResponse):
        self.session = session
        self.ws_ctx_builder = ws_ctx_builder
        self.response_cls = response_cls
        self.on_enter = on_enter
        self._ws_ctx = None

    async def __aenter__(self):
        max_retries = len(self.session.config.endpoints)
        retry_count = 0
        while True:
            try:
                retry_count += 1
                self._ws_ctx = self.ws_ctx_builder()
                raw_ws = await self._ws_ctx.__aenter__()
            except aiohttp.ClientConnectionError as e:
                if retry_count == max_retries:
                    msg = 'Request to the API endpoint has failed.\n' \
                          'Check your network connection and/or the server status.\n' \
                          'Error detail: {!r}'.format(e)
                    raise BackendClientError(msg) from e
                else:
                    self.session.config.rotate_endpoints()
                    continue
            except aiohttp.ClientResponseError as e:
                msg = 'API endpoint response error.\n' \
                      '\u279c {!r}'.format(e)
                raise BackendClientError(msg) from e
            else:
                break

        wrapped_ws = self.response_cls(self.session, raw_ws)
        if self.on_enter is not None:
            await self.on_enter(wrapped_ws)
        return wrapped_ws

    async def __aexit__(self, *args):
        ret = await self._ws_ctx.__aexit__(*args)
        self._ws_ctx = None
        return ret


class SSEResponse(Response):

    __slots__ = (
        '_session', '_raw_response', '_async_mode',
        '_auto_reconnect',
    )

    def __init__(self, session: BaseSession,
                 underlying_response: aiohttp.ClientResponse):
        super().__init__(session, underlying_response, async_mode=True)

    async def fetch_events(self):
        msg_lines = []
        while True:
            line = await self._raw_response.content.readline()
            if not line:
                # connection closed
                break
            line = line.strip(b'\r\n')
            if line.startswith(b':'):
                # comment
                continue
            if not line:
                # message boundary
                if len(msg_lines) == 0:
                    continue
                evdata = {
                    'event': 'message',
                    'data': '',
                }
                data_lines = []
                try:
                    for line in msg_lines:
                        hdr, text = line.split(':', maxsplit=1)
                        text = text.lstrip(' ')
                        if hdr == 'data':
                            data_lines.append(text)
                        elif hdr == 'event':
                            evdata['event'] = text
                        elif hdr == 'id':
                            evdata['id'] = text
                        elif hdr == 'retry':
                            evdata['retry'] = int(text)
                except (IndexError, ValueError):
                    log.exception('SSEResponse: parsing-error')
                    continue
                evdata['data'] = '\n'.join(data_lines)
                msg_lines.clear()
                yield evdata
            else:
                msg_lines.append(line.decode('utf-8'))


class SSEContextManager:

    __slots__ = (
        'session', 'rqst_ctx_builder', 'response_cls',
        '_rqst_ctx',
    )

    def __init__(self, session: BaseSession,
                 rqst_ctx_builder: Callable[[], _RequestContextManager], *,
                 response_cls: SSEResponse = SSEResponse):
        self.session = session
        self.rqst_ctx_builder = rqst_ctx_builder
        self.response_cls = response_cls
        self._rqst_ctx = None

    async def __aenter__(self):
        max_retries = len(self.session.config.endpoints)
        retry_count = 0
        while True:
            try:
                retry_count += 1
                self._rqst_ctx = self.rqst_ctx_builder()
                raw_resp = await self._rqst_ctx.__aenter__()
                if raw_resp.status // 100 != 2:
                    msg = await raw_resp.text()
                    raise BackendAPIError(raw_resp.status, raw_resp.reason, msg)
                return self.response_cls(self.session, raw_resp)
            except aiohttp.ClientConnectionError as e:
                if retry_count == max_retries:
                    msg = 'Request to the API endpoint has failed.\n' \
                          'Check your network connection and/or the server status.\n' \
                          '\u279c {!r}'.format(e)
                    raise BackendClientError(msg) from e
                else:
                    self.session.config.rotate_endpoints()
                    continue
            except aiohttp.ClientResponseError as e:
                msg = 'API endpoint response error.\n' \
                      '\u279c {!r}'.format(e)
                raise BackendClientError(msg) from e

    async def __aexit__(self, *args):
        ret = await self._rqst_ctx.__aexit__(*args)
        self._rqst_ctx = None
        return ret
