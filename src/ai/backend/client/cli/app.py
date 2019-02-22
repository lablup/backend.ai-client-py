import asyncio
import signal
import functools
import aiohttp
import click
import os
import shutil
import json

from . import main
from .pretty import print_info, print_error
from ..request import Request
from ..session import AsyncSession
from ..compat import asyncio_run_forever, current_loop
from ..kernel import StreamPty


class IpythonClient:
    STDIN_FILENO = 0
    STDOUT_FILENO = 1
    def __init__(self, session_id):
        self.loop = current_loop()
        self.stream = None
        self.session_id = session_id

        def signal_handler(signame):
            if signame == 'SIGTERM':
                sys.exit(0)
            else:
                asyncio.run_coroutine_threadsafe(self.stream.send_signal(signame), self.loop)
        for signame in ['SIGINT', 'SIGTSTP', 'SIGTERM']:
            self.loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(signal_handler, signame))
        
        def listen_stdin():
            data = os.read(self.STDIN_FILENO, 1024)
            data = data.decode()
            asyncio.run_coroutine_threadsafe(self.stream.send_stdin(data), self.loop)
        self.loop.add_reader(self.STDIN_FILENO, listen_stdin)
    
    def start(self):
        async def listen_ws():
            async with AsyncSession() as session:
                async with session.Kernel(self.session_id).stream_pty() as _stream:
                    self.stream = _stream
                    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
                    await self.stream.resize(rows, cols)
                    async for msg in self.stream:
                        data = json.loads(msg.data)
                        os.write(self.STDOUT_FILENO, data['bytes'])
        self.loop.create_task(listen_ws())
        self.loop.run_forever()

class WSProxy:
    __slots__ = (
        'api_session', 'session_id',
        'app_name', 'protocol',
        'reader', 'writer',
        'down_task',
    )
    BUFFER_SIZE = 8192

    def __init__(self, api_session: AsyncSession,
                 session_id: str,
                 app_name: str,
                 protocol: str,
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        self.api_session = api_session
        self.session_id = session_id
        self.app_name = app_name
        self.protocol = protocol
        self.reader = reader
        self.writer = writer
        self.down_task = None

    async def run(self):
        path = "/stream/kernel/{0}/{1}proxy".format(self.session_id, self.protocol)
        api_rqst = Request(
            self.api_session, "GET", path, b'',
            params={'app': self.app_name},
            content_type="application/json")
        async with api_rqst.connect_websocket() as ws:

            async def downstream():
                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.ERROR:
                            await self.write_error(msg)
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            if msg.data != aiohttp.WSCloseCode.OK:
                                await self.write_error(msg)
                            break
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            self.writer.write(msg.data)
                            await self.writer.drain()
                except ConnectionResetError:
                    pass  # shutting down
                except asyncio.CancelledError:
                    raise
                finally:
                    self.writer.close()
                    if hasattr(self.writer, 'wait_closed'):  # Python 3.7+
                        await self.writer.wait_closed()

            self.down_task = asyncio.ensure_future(downstream())
            try:
                while True:
                    chunk = await self.reader.read(self.BUFFER_SIZE)
                    if not chunk:
                        break
                    await ws.send_bytes(chunk)
            except ConnectionResetError:
                pass  # shutting down
            except asyncio.CancelledError:
                raise
            finally:
                if not self.down_task.done():
                    await self.down_task
                    self.down_task = None

    async def write_error(self, msg):
        rsp = 'HTTP/1.1 503 Service Unavailable\r\n' \
            'Connection: Closed\r\n\r\n' \
            'WebSocket reply: {}'.format(msg.data.decode('utf8'))
        self.writer.write(rsp.encode())
        await self.writer.drain()


class ProxyRunner:
    __slots__ = (
        'session_id', 'app_name',
        'protocol', 'host', 'port',
        'api_session', 'local_server', 'loop',
    )

    def __init__(self, api_session, session_id, app_name,
                 protocol, host, port, *, loop=None):
        self.api_session = api_session
        self.session_id = session_id
        self.app_name = app_name
        self.protocol = protocol
        self.host = host
        self.port = port
        self.local_server = None
        self.loop = loop if loop else current_loop()

    async def handle_connection(self, reader, writer):
        p = WSProxy(self.api_session, self.session_id,
                    self.app_name, self.protocol,
                    reader, writer)
        try:
            await p.run()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print_error(e)

    async def ready(self):
        self.local_server = await asyncio.start_server(
            self.handle_connection, self.host, self.port,
            loop=self.loop)

    async def close(self):
        self.local_server.close()
        await self.local_server.wait_closed()


@main.command()
@click.argument('session_id', type=str, metavar='SESSID')
@click.argument('app', type=str)
@click.option('--bind', type=str, default='127.0.0.1',
              help='The IP/host address to bind this proxy.')
@click.option('-p', '--port', type=int, default=8080,
              help='The port number to listen user connections.')
def app(session_id, app, bind, port):
    """
    Run a local proxy to a service provided by Backend.AI compute sessions.

    The type of proxy depends on the app definition: plain TCP or HTTP.

    \b
    SESSID: The compute session ID.
    APP: The name of service provided by the given session.
    """
    if app == 'ipython':
        print_info("ipython kernel started. type ^\ to exit")
        IpythonClient(session_id).start()
    else:
        api_session = None
        runner = None

        async def app_setup():
            nonlocal api_session, runner
            loop = current_loop()
            api_session = AsyncSession()
            # TODO: generalize protocol using service ports metadata
            protocol = 'http'
            runner = ProxyRunner(api_session, session_id, app,
                                protocol, bind, port,
                                loop=loop)
            await runner.ready()
            print_info(
                "A local proxy to the application \"{0}\" ".format(app) +
                "provided by the session \"{0}\" ".format(session_id) +
                "is available at: {0}://{1}:{2}"
                .format(protocol, bind, port)
            )

        async def app_shutdown():
            nonlocal api_session, runner
            print_info("Shutting down....")
            await runner.close()
            await api_session.close()
            print_info("The local proxy to \"{}\" has terminated."
                    .format(app))

        asyncio_run_forever(app_setup(), app_shutdown(),
                            stop_signals={signal.SIGINT, signal.SIGTERM})

