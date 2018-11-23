from argparse import Namespace

import aiohttp
from aiohttp import web
import pytest

from ai.backend.client import config
from ai.backend.client.cli.proxy import proxy as proxy_command


@pytest.fixture
def api_app(event_loop):
    app = web.Application()
    recv_queue = []

    async def echo_ws(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                recv_queue.append(msg)
                await ws.send_str(msg.data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                recv_queue.append(msg)
                await ws.send_bytes(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                recv_queue.append(msg)
        return ws

    async def echo_web(request):
        body = await request.read()
        resp = web.Response(status=200, reason='Good', body=body)
        resp.headers['Content-Type'] = request.content_type
        return resp

    app.router.add_route('GET', r'/stream/echo', echo_ws)
    app.router.add_route('POST', r'/echo', echo_web)
    runner = web.AppRunner(app)

    async def start(port):
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', port)
        await site.start()
        return app, recv_queue

    async def shutdown():
        await runner.cleanup()

    try:
        yield start
    finally:
        event_loop.run_until_complete(shutdown())


@pytest.fixture
def proxy_app(event_loop):
    args = Namespace()
    args.testing = True
    app = proxy_command(args)
    runner = web.AppRunner(app)

    async def start(port):
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', port)
        await site.start()
        return app

    async def shutdown():
        await runner.cleanup()

    try:
        yield start
    finally:
        event_loop.run_until_complete(shutdown())


@pytest.mark.asyncio
async def test_proxy_web(monkeypatch, example_keypair, api_app, proxy_app,
                         unused_tcp_port_factory):
    api_port = unused_tcp_port_factory()
    api_url = 'http://127.0.0.1:{}'.format(api_port)
    monkeypatch.setenv('BACKEND_ACCESS_KEY', example_keypair[0])
    monkeypatch.setenv('BACKEND_SECRET_KEY', example_keypair[1])
    monkeypatch.setenv('BACKEND_ENDPOINT', api_url)
    monkeypatch.setattr(config, '_config', config.APIConfig())
    api_app, recv_queue = await api_app(api_port)
    proxy_client = aiohttp.ClientSession()
    proxy_port = unused_tcp_port_factory()
    proxy_app = await proxy_app(proxy_port)
    proxy_url = 'http://127.0.0.1:{}'.format(proxy_port)
    data = {"test": 1234}
    async with proxy_client.request('POST', proxy_url + '/echo',
                                    json=data) as resp:
        assert resp.status == 200
        assert resp.reason == 'Good'
        ret = await resp.json()
        assert ret['test'] == 1234


@pytest.mark.asyncio
async def test_proxy_web_502(monkeypatch, example_keypair, proxy_app,
                             unused_tcp_port_factory):
    api_port = unused_tcp_port_factory()
    api_url = 'http://127.0.0.1:{}'.format(api_port)
    monkeypatch.setenv('BACKEND_ACCESS_KEY', example_keypair[0])
    monkeypatch.setenv('BACKEND_SECRET_KEY', example_keypair[1])
    monkeypatch.setenv('BACKEND_ENDPOINT', api_url)
    monkeypatch.setattr(config, '_config', config.APIConfig())
    # Skip creation of api_app; let the proxy use a non-existent server.
    proxy_client = aiohttp.ClientSession()
    proxy_port = unused_tcp_port_factory()
    proxy_app = await proxy_app(proxy_port)
    proxy_url = 'http://127.0.0.1:{}'.format(proxy_port)
    data = {"test": 1234}
    async with proxy_client.request('POST', proxy_url + '/echo',
                                    json=data) as resp:
        assert resp.status == 502
        assert resp.reason == 'Bad Gateway'


@pytest.mark.asyncio
async def test_proxy_websocket(monkeypatch, example_keypair, api_app, proxy_app,
                               unused_tcp_port_factory):
    api_port = unused_tcp_port_factory()
    api_url = 'http://127.0.0.1:{}'.format(api_port)
    monkeypatch.setenv('BACKEND_ACCESS_KEY', example_keypair[0])
    monkeypatch.setenv('BACKEND_SECRET_KEY', example_keypair[1])
    monkeypatch.setenv('BACKEND_ENDPOINT', api_url)
    monkeypatch.setattr(config, '_config', config.APIConfig())
    api_app, recv_queue = await api_app(api_port)
    proxy_client = aiohttp.ClientSession()
    proxy_port = unused_tcp_port_factory()
    proxy_app = await proxy_app(proxy_port)
    proxy_url = 'http://127.0.0.1:{}'.format(proxy_port)
    ws = await proxy_client.ws_connect(proxy_url + '/stream/echo')
    await ws.send_str('test')
    assert await ws.receive_str() == 'test'
    await ws.send_bytes(b'\x00\x00')
    assert await ws.receive_bytes() == b'\x00\x00'
    assert recv_queue[0].type == aiohttp.WSMsgType.TEXT
    assert recv_queue[0].data == 'test'
    assert recv_queue[1].type == aiohttp.WSMsgType.BINARY
    assert recv_queue[1].data == b'\x00\x00'
    await ws.close()
