import asyncio
import aiohttp
import binascii
import os
from ..request import Request
from ..session import Session, AsyncSession
from ..compat import token_hex
from ..exceptions import BackendError
from aiohttp import web
from datetime import datetime
from dateutil.tz import tzutc
from .pretty import print_info, print_fail

from . import register_command


class WSProxy(Request):
    __slots__ = ['conn', 'down_conn', 'upstream_buffer', 'upstream_buffer_task']

    def __init__(self, session, path):
        super(WSProxy, self).__init__(session, "GET", path)

    async def init(self, r, w):
        self.reader = r
        self.writer = w

    async def run(self):
        self.date = datetime.now(tzutc())
        self.headers['Date'] = self.date.isoformat()
        self._sign()
        url = self.build_url()
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url, headers=self.headers) as ws:
                async def up():
                    try:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.ERROR:
                                self.write_error_and_close()
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSE:
                                if msg.data != aiohttp.WSCloseCode.OK:
                                    self.write_error_and_close()
                                break
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                self.writer.write(msg.data)
                                await self.writer.drain()
                    finally:
                        self.writer.close()
                        await ws.close()

                asyncio.ensure_future(up())

                while True:
                    try:
                        chunk = await self.reader.read(8192)
                        if not chunk:
                            break
                        await ws.send_bytes(chunk)
                    except GeneratorExit:
                        break

        await self.close()

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def write_error_and_close(self):
        rsp = 'HTTP/1.1 503 Service Unavailable\n' \
            'Connection: Closed\n' \
            '\n' \
            'Service Unavailable\n'
        self.writer.write(rsp.encode())
        await self.writer.drain()
        self.writer.close()
        await writer.wait_closed()


def run_proxy(session, kernel, host, port):
    loop = asyncio.get_event_loop()

    async def connection_handler(reader, writer):
        session_id = kernel.kernel_id
        path = f'/wsproxy/{session_id}/stream'
        p = WSProxy(session, path)
        await p.init(reader, writer)
        await p.run()

    print_info(f"http://{host}:{port}")
    coro = asyncio.start_server(connection_handler, host, port, loop=loop)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    print_info("Shutting down....")
    server.close()
    loop.run_until_complete(server.wait_closed())


def destroy_kernel(kernel):
    kernel.destroy()


@register_command
def app(args):
    """
    Run the web app via backend.ai
    """
    app = args.app
    host = args.bind
    port = args.port
    session = Session()
    try:
        kernel_id = token_hex(16)
        kernel = session.Kernel.get_or_create(
            f"app-{app}", client_token=kernel_id)
        print_info(f"Started with session id - {kernel_id}")
    except BackendError as e:
        print_fail(str(e))
        session.close()
        return
    run_proxy(session, kernel, host, port)
    destroy_kernel(kernel)
    session.close()
    print("Done")


app.add_argument('app',
                 help='Run an app via http (BETA)')

app.add_argument('--bind', type=str, default='localhost',
                   help='The IP/host address to bind this proxy.')
app.add_argument('-p', '--port', type=int, default=8080,
                   help='The TCP port to accept non-encrypted non-authorized '
                        'API requests.')

