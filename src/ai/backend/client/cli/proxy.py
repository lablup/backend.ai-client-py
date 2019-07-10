import asyncio
import json
import re

import aiohttp
from aiohttp import web
import click

from . import main
from .pretty import print_info, print_error, print_fail
from ..exceptions import BackendAPIError, BackendClientError
from ..request import Request
from ..session import AsyncSession


class WebSocketProxy:
    __slots__ = (
        'up_conn', 'down_conn',
        'upstream_buffer', 'upstream_buffer_task',
    )

    def __init__(self, up_conn: aiohttp.ClientWebSocketResponse,
                 down_conn: web.WebSocketResponse):
        self.up_conn = up_conn
        self.down_conn = down_conn
        self.upstream_buffer = asyncio.Queue()
        self.upstream_buffer_task = None

    async def proxy(self):
        asyncio.ensure_future(self.downstream())
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
            # here, client gracefully disconnected
        except asyncio.CancelledError:
            # here, client forcibly disconnected
            pass
        finally:
            await self.close_downstream()

    async def downstream(self):
        try:
            self.upstream_buffer_task = \
                    asyncio.ensure_future(self.consume_upstream_buffer())
            print_info("websocket proxy started")
            async for msg in self.up_conn:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.down_conn.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await self.down_conn.send_bytes(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
            # here, server gracefully disconnected
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print_fail('unexpected error: {}'.format(e))
        finally:
            await self.close_upstream()
            print_info("websocket proxy termianted")

    async def consume_upstream_buffer(self):
        try:
            while True:
                data, tp = await self.upstream_buffer.get()
                if not self.up_conn.closed:
                    if tp == aiohttp.WSMsgType.BINARY:
                        await self.up_conn.send_bytes(data)
                    elif tp == aiohttp.WSMsgType.TEXT:
                        await self.up_conn.send_str(data)
        except asyncio.CancelledError:
            pass

    async def send(self, msg: str, tp: aiohttp.WSMsgType):
        await self.upstream_buffer.put((msg, tp))

    async def close_downstream(self):
        if not self.down_conn.closed:
            await self.down_conn.close()

    async def close_upstream(self):
        if not self.upstream_buffer_task.done():
            self.upstream_buffer_task.cancel()
            await self.upstream_buffer_task
        if not self.up_conn.closed:
            await self.up_conn.close()


async def web_handler(request):
    session = request.app['client_session']
    path = re.sub(r'^/?v(\d+)/', '/', request.path)
    try:
        # We treat all requests and responses as streaming universally
        # to be a transparent proxy.
        api_rqst = Request(
            session, request.method, path, request.content,
            params=request.query,
            content_type=request.content_type)
        # Uploading request body happens at the entering of the block,
        # and downloading response body happens in the read loop inside.
        async with api_rqst.fetch() as up_resp:
            down_resp = web.StreamResponse()
            down_resp.set_status(up_resp.status, up_resp.reason)
            down_resp.headers.update(up_resp.headers)
            down_resp.headers['Access-Control-Allow-Origin'] = '*'
            await down_resp.prepare(request)
            while True:
                chunk = await up_resp.aread(8192)
                if not chunk:
                    break
                await down_resp.write(chunk)
            return down_resp
    except BackendAPIError as e:
        return web.Response(body=json.dumps(e.data),
                            status=e.status, reason=e.reason)
    except BackendClientError:
        return web.Response(
            body="The proxy target server is inaccessible.",
            status=502,
            reason="Bad Gateway")
    except asyncio.CancelledError:
        return web.Response(
            body="The proxy is being shut down.",
            status=503,
            reason="Service Unavailable")
    except Exception as e:
        print_error(e)
        return web.Response(
            body="Something has gone wrong.",
            status=500,
            reason="Internal Server Error")


async def websocket_handler(request):
    session = request.app['client_session']
    path = re.sub(r'^/?v(\d+)/', '/', request.path)
    try:
        api_rqst = Request(
            session, request.method, path, request.content,
            params=request.query,
            content_type=request.content_type)
        async with api_rqst.connect_websocket() as up_conn:
            down_conn = web.WebSocketResponse()
            await down_conn.prepare(request)
            web_socket_proxy = WebSocketProxy(up_conn, down_conn)
            await web_socket_proxy.proxy()
            return down_conn
    except BackendAPIError as e:
        return web.Response(body=json.dumps(e.data),
                            status=e.status, reason=e.reason)
    except BackendClientError:
        return web.Response(
            body="The proxy target server is inaccessible.",
            status=502,
            reason="Bad Gateway")
    except asyncio.CancelledError:
        return web.Response(
            body="The proxy is being shut down.",
            status=503,
            reason="Service Unavailable")
    except Exception as e:
        print_error(e)
        return web.Response(
            body="Something has gone wrong.",
            status=500,
            reason="Internal Server Error")


async def startup_proxy(app):
    app['client_session'] = AsyncSession()


async def cleanup_proxy(app):
    await app['client_session'].close()


def create_proxy_app():
    app = web.Application()
    app.on_startup.append(startup_proxy)
    app.on_cleanup.append(cleanup_proxy)

    app.router.add_route("GET", r'/stream/{path:.*$}', websocket_handler)
    app.router.add_route("GET", r'/wsproxy/{path:.*$}', websocket_handler)
    app.router.add_route('*', r'/{path:.*$}', web_handler)
    return app


@main.command(context_settings=dict(allow_extra_args=True))
@click.option('--bind', type=str, default='localhost',
              help='The IP/host address to bind this proxy.')
@click.option('-p', '--port', type=int, default=8084,
              help='The TCP port to accept non-encrypted non-authorized '
                   'API requests.')
@click.pass_context
def proxy(ctx, bind, port):
    """
    Run a non-encrypted non-authorized API proxy server.
    Use this only for development and testing!
    """
    app = create_proxy_app()
    web.run_app(app, host=bind, port=port)
