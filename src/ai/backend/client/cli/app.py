import asyncio
import aiohttp
from ..request import Request
from ..session import AsyncSession
from ..compat import token_hex
from .pretty import print_info

from . import register_command


class WSProxy:
    __slots__ = ('conn', 'down_conn', 'upstream_buffer', 'upstream_buffer_task', 'reader', 'writer', 'session', 'path')
    BUFFER_SIZE = 8192

    def __init__(self, session: AsyncSession, kernel, reader, writer):
        self.session = session
        self.path = f"/wsproxy/{kernel.kernel_id}/stream"
        self.reader = reader
        self.writer = writer

    async def run(self):
        api_rqst = Request(
            self.session, "GET", self.path, b'',
            content_type="application/json")
        async with api_rqst.connect_websocket() as ws:
            async def up():
                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.ERROR:
                            await self.write_error_and_close()
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            if msg.data != aiohttp.WSCloseCode.OK:
                                await self.write_error_and_close()
                            break
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            self.writer.write(msg.data)
                            await self.writer.drain()
                finally:
                    self.writer.close()
                    await ws.close()
            task = asyncio.ensure_future(up())
            while True:
                try:
                    chunk = await self.reader.read(self.BUFFER_SIZE)
                    if not chunk:
                        break
                    await ws.send_bytes(chunk)
                except GeneratorExit:
                    break

        await self.close()

    async def close(self):
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()

    async def write_error_and_close(self):
        rsp = 'HTTP/1.1 503 Service Unavailable\n' \
            'Connection: Closed\n' \
            '\n' \
            'Service Unavailable\n'
        self.writer.write(rsp.encode())
        await self.close()


class ProxyRunner:
    __slots__ = ('app_name', 'host', 'port', 'session', 'kernel', 'server', 'loop')

    def __init__(self, name, host, port, loop=asyncio.get_event_loop()):
        self.app_name = name
        self.host = host
        self.port = port
        self.loop = loop

    async def ready(self):
        self.session = AsyncSession()
        kernel_id = token_hex(16)
        self.kernel = await self.session.Kernel.get_or_create(
            f"app-{self.app_name}", client_token=kernel_id)
        print_info(f"Started with session id - {kernel_id}")

        async def connection_handler(reader, writer):
            p = WSProxy(self.session, self.kernel, reader, writer)
            await p.run()

        print_info(f"http://{self.host}:{self.port}")
        self.server = await asyncio.start_server(connection_handler, self.host, self.port, loop=self.loop)

    async def close(self):
        self.server.close()
        await self.server.wait_closed()
        await self.kernel.destroy()
        await self.session.close()


@register_command
def app(args):
    """
    Run the web app via backend.ai
    """

    loop = asyncio.get_event_loop()
    r = ProxyRunner(args.app, args.bind, args.port, loop)
    loop.run_until_complete(r.ready())
    try:
        loop.run_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    print_info("Shutting down....")
    loop.run_until_complete(r.close())
    print_info("Done")


app.add_argument('app',
                 help='Run an app via http (BETA)')
app.add_argument('--bind', type=str, default='localhost',
                   help='The IP/host address to bind this proxy.')
app.add_argument('-p', '--port', type=int, default=8080,
                   help='The TCP port to accept non-encrypted non-authorized '
                        'API requests.')
