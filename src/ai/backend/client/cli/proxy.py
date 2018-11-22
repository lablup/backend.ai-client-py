import asyncio
import re
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence, Union

import aiohttp
from aiohttp import web
from aiohttp.client_exceptions import ClientResponseError, ClientConnectorError
from dateutil.tz import tzutc

from . import register_command
from ..config import APIConfig
from .pretty import print_info, print_fail
from ..exceptions import BackendClientError
from ..request import Request, StreamingResponse
from ..session import AsyncSession


class RawRequest(Request):
    __slots__ = ('config', 'method', 'path',
                 'date', 'headers',
                 'content_type', '_content', 'reporthook')

    def __init__(self, session: AsyncSession,
                 method: str = 'GET',
                 path: str = None,
                 content: Mapping = None,
                 config: APIConfig = None,
                 reporthook: Callable = None,
                 content_type: str = None) -> None:
        self.content_type = content_type
        super().__init__(session, method, path, content, config, reporthook)

    @property
    def content(self) -> Union[aiohttp.StreamReader, bytes, bytearray, None]:
        if(isinstance(self.content, aiohttp.StreamReader)):
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
            if 'Content-Length' in self.headers:
                del self.headers['Content-Length']
            self.headers['Content-Type'] = self.content_type
            self.content_type = "multipart/form-data"
        else:
            Request.content.fset(self, value)

    def pack_content(self):
        if(isinstance(self.content, aiohttp.StreamReader)):
            return self._content
        super(RawRequest, self).pack_content(self)


class WebSocketProxy(Request):
    __slots__ = (
        'up_conn', 'down_conn',
        'upstream_buffer', 'upstream_buffer_task',
        'downstream_task',
    )

    def __init__(self, session: AsyncSession,
                 path: str,
                 ws: web.WebSocketResponse):
        super().__init__(session, "GET", path)
        self.up_conn = None
        self.down_conn = ws
        self.upstream_buffer = asyncio.PriorityQueue()
        self.upstream_buffer_task = None
        self.downstream_task = None

    async def proxy(self):
        self.downstream_task = asyncio.ensure_future(self.downstream())
        await self.upstream()

    async def upstream(self):
        try:
            async for msg in self.down_conn:
                if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                    await self.send(msg.data, msg.type)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print_fail("ws connection closed with exception {}"
                               .format(self.up_conn.exception()))
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    break
        finally:
            await self.close()

    async def downstream(self):
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        self._sign()
        path = self.build_url()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(path, headers=self.headers) as ws:
                    self.up_conn = ws
                    self.upstream_buffer_task = \
                            asyncio.ensure_future(self.consume_upstream_buffer())
                    print_info("websocket proxy started")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self.down_conn.send_str(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await self.down_conn.send_bytes(msg.data)
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
        except ClientConnectorError:
            print_fail("websocket connection failed")
            await self.down_conn.close(code=503, message="Connection failed")
        except ClientResponseError as e:
            print_fail("websocket response error - {}".format(e.status))
            await self.down_conn.close(code=e.status, message=e.message)
        finally:
            await self.close()
            print_info("websocket proxy termianted")

    async def consume_upstream_buffer(self):
        while True:
            data, tp = await self.upstream_buffer.get()
            if self.up_conn:
                if tp == aiohttp.WSMsgType.BINARY:
                    await self.up_conn.send_bytes(data)
                elif tp == aiohttp.WSMsgType.TEXT:
                    await self.up_conn.send_str(data)
            else:
                await self.close()

    async def send(self, msg: str, tp: aiohttp.WSMsgType):
        await self.upstream_buffer.put((msg, tp))

    async def close(self):
        if self.upstream_buffer_task and not self.upstream_buffer_task.done():
            self.upstream_buffer_task.cancel()
            await self.upstream_buffer_task
        if self.downstream_task and not self.downstream_task.done():
            self.downstream_task.cancel()
            await self.downstream_task
        if self.up_conn:
            await self.up_conn.close()
        if not self.down_conn.closed:
            await self.down_conn.close()
        self.up_conn = None


async def web_handler(request):
    session = request.app['client_session']
    content_type = request.headers.get('Content-Type', "")
    try:
        if re.match('multipart/form-data', content_type):
            body = request.content
            api_rqst = RawRequest(session, request.method, request.path,
                                  body, content_type=content_type)
        else:
            body = await request.read()
            api_rqst = Request(session, request.method, request.path, body)
        resp = await api_rqst.afetch()
    except BackendClientError:
        resp = web.Response(
            body="The proxy target server is inaccessible.",
            status=502,
            reason="Bad Gateway")
        return resp

    down_resp = web.StreamResponse()
    down_resp.set_status(resp.status, resp.reason)
    down_resp.headers.update(resp.headers)
    down_resp.headers['Access-Control-Allow-Origin'] = '*'
    await down_resp.prepare(request)
    if isinstance(resp, StreamingResponse):
        while True:
            chunk = await resp.read(8192)
            if not chunk:
                break
            await down_resp.write(chunk)
    else:
        await down_resp.write(resp.content)
    return down_resp


async def websocket_handler(request):
    path = re.sub(r'^/?v(\d+)/', '/', request.path)
    session = request.app['client_session']
    ws = web.WebSocketResponse(autoclose=False)
    web_socket_proxy = WebSocketProxy(session, path, ws)
    await ws.prepare(request)
    await web_socket_proxy.proxy()
    return ws


async def startup_proxy(app):
    app['client_session'] = AsyncSession()


async def cleanup_proxy(app):
    await app['client_session'].close()


@register_command
def proxy(args):
    """
    Run a non-encrypted non-authorized API proxy server.
    Use this only for development and testing!
    """
    app = web.Application()
    app.on_startup.append(startup_proxy)
    app.on_cleanup.append(cleanup_proxy)

    app.router.add_route("GET", r'/stream/{path:.*$}', websocket_handler)
    app.router.add_route("GET", r'/wsproxy/{path:.*$}', websocket_handler)
    app.router.add_route('*', r'/{path:.*$}', web_handler)
    web.run_app(app, host=args.bind, port=args.port)


proxy.add_argument('--bind', type=str, default='localhost',
                   help='The IP/host address to bind this proxy.')
proxy.add_argument('-p', '--port', type=int, default=8084,
                   help='The TCP port to accept non-encrypted non-authorized '
                        'API requests.')
