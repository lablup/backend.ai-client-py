import asyncio
from collections import OrderedDict
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence, Union

import aiohttp
import aiohttp.web
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc
from multidict import CIMultiDict
import json

from .auth import generate_signature
from .config import APIConfig, get_config
from .exceptions import BackendClientError

__all__ = [
    'Request',
    'Response',
]


class BaseRequest:

    __slots__ = ['config', 'method', 'path',
                 'date', 'headers',
                 'content_type', '_content']

    _allowed_methods = frozenset([
        'GET', 'HEAD', 'POST',
        'PUT', 'PATCH', 'DELETE',
        'OPTIONS'])

    def __init__(self, method: str='GET',
                 path: str=None,
                 content: Mapping=None,
                 config: APIConfig=None,
                 reporthook: Callable=None) -> None:
        '''
        Initialize an API request.

        :param str path: The query path. When performing requests, the version number
                         prefix will be automatically perpended if required.

        :param Mapping content: The API query body which will be encoded as JSON.

        :param APIConfig config: The API configuration.  If set to ``None``, it will
                                 use the global configuration which is read from the
                                 environment variables.
        '''
        self.config = config if config else get_config()
        self.method = method
        if path.startswith('/'):
            path = path[1:]
        self.path = path
        self.date = None
        self.headers = CIMultiDict([
            ('User-Agent', self.config.user_agent),
            ('X-BackendAI-Version', self.config.version),
        ])
        self.content = content if content is not None else b''
        self.reporthook = reporthook

    @property
    def content(self) -> Union[bytes, bytearray, None]:
        '''
        Retrieves the content in the original form.
        Private codes should NOT use this as it incurs duplicate
        encoding/decoding.
        '''
        if self._content is None:
            raise ValueError('content is not set.')
        if self.content_type == 'application/octet-stream':
            return self._content
        elif self.content_type == 'application/json':
            return json.loads(self._content.decode('utf-8'),
                              object_pairs_hook=OrderedDict)
        elif self.content_type == 'text/plain':
            return self._content.decode('utf-8')
        elif self.content_type == 'multipart/form-data':
            return self._content
        else:
            raise RuntimeError('should not reach here')  # pragma: no cover

    @content.setter
    def content(self, value: Union[bytes, bytearray,
                                   Mapping[str, Any],
                                   Sequence[Any],
                                   None]):
        '''
        Sets the content of the request.
        Depending on the type of content, it automatically sets appropriate
        headers such as content-type and content-length.
        '''
        if isinstance(value, (bytes, bytearray)):
            self.content_type = 'application/octet-stream'
            self._content = value
            self.headers['Content-Type'] = self.content_type
            self.headers['Content-Length'] = str(len(self._content))
        elif isinstance(value, str):
            self.content_type = 'text/plain'
            self._content = value.encode('utf-8')
            self.headers['Content-Type'] = self.content_type
            self.headers['Content-Length'] = str(len(self._content))
        elif isinstance(value, (dict, OrderedDict)):
            self.content_type = 'application/json'
            self._content = json.dumps(value).encode('utf-8')
            self.headers['Content-Type'] = self.content_type
            self.headers['Content-Length'] = str(len(self._content))
        elif isinstance(value, (list, tuple)):
            self.content_type = 'multipart/form-data'
            self._content = value
            # Let the http client library decide the header values.
            # (e.g., message boundaries)
            if 'Content-Length' in self.headers:
                del self.headers['Content-Length']
            if 'Content-Type' in self.headers:
                del self.headers['Content-Type']
        else:
            raise TypeError('Unsupported content value type.')

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

    def build_url(self):
        base_url = self.config.endpoint.path.rstrip('/')
        major_ver = self.config.version.split('.', 1)[0]
        query_path = self.path.lstrip('/') if len(self.path) > 0 else ''
        path = '{0}/{1}/{2}'.format(base_url, major_ver, query_path)
        canonical_url = self.config.endpoint.with_path(path)
        return str(canonical_url)

    # TODO: attach rate-limit information

    def send(self, *args, loop=None, **kwargs):
        '''
        Sends the request to the server.
        '''
        loop = loop if loop is not None else asyncio.get_event_loop()
        return loop.run_until_complete(self.asend(*args, **kwargs))

    async def asend(self, *, sess=None, timeout=None):
        '''
        Sends the request to the server.

        This method is a coroutine.
        '''
        assert self.method in self._allowed_methods
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        owns_session = False
        if sess is None:
            owns_session = True
            session = aiohttp.ClientSession()
        else:
            assert isinstance(session, aiohttp.ClientSession)
            session = sess
        try:
            self._sign()
            async with _timeout(timeout):
                rqst_ctx = session.request(
                    self.method,
                    self.build_url(),
                    data=self.pack_content(),
                    headers=self.headers)
                async with rqst_ctx as resp:
                    body = await resp.read()
                    return Response(resp.status, resp.reason,
                                    body=body,
                                    content_type=resp.content_type,
                                    charset=resp.charset)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These exceptions must be bubbled up.
            raise
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e
        finally:
            if owns_session:
                await session.close()

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

    async def connect_websocket(self, *, sess=None):
        '''
        Creates a WebSocket connection.

        This method is a coroutine.
        '''
        assert self.method == 'GET'
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        owns_session = False
        if sess is None:
            owns_session = True
            session = aiohttp.ClientSession()
        else:
            assert isinstance(session, aiohttp.ClientSession)
            session = sess
        try:
            self._sign()
            ws = await session.ws_connect(self.build_url(), headers=self.headers)
            return session, ws
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These exceptions must be bubbled up.
            raise
        except aiohttp.ClientError as e:
            msg = 'Request to the API endpoint has failed.\n' \
                  'Check your network connection and/or the server status.'
            raise BackendClientError(msg) from e
        finally:
            if owns_session:
                await session.close()


class Request(BaseRequest):
    pass


class Response:

    __slots__ = ['_status', '_reason',
                 '_content_type', '_content_length', '_charset',
                 '_body']

    def __init__(self, status: int, reason: str, *,
                 body: Union[bytes, bytearray]=b'',
                 content_type='text/plain',
                 content_length=None,
                 charset=None):
        self._status = status
        self._reason = reason
        if not isinstance(body, (bytes, bytearray)):
            raise ValueError('body must be a bytes-like object.')
        self._body = body
        self._content_type = content_type
        self._content_length = content_length
        self._charset = charset if charset else 'utf-8'

        # TODO: include rate-limiting information from headers

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    @property
    def content_type(self):
        return self._content_type

    @property
    def content_length(self):
        is_multipart = self._content_type.startswith('multipart/')
        if self._content_length is None and not is_multipart:
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
        return loads(self._body.decode(self._charset), object_pairs_hook=OrderedDict)
