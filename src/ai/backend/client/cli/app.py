import asyncio
import json
import signal
from typing import MutableMapping

import aiohttp
import click

from . import main
from .pretty import print_info, print_warn, print_error
from ..config import DEFAULT_CHUNK_SIZE
from ..request import Request
from ..session import AsyncSession
from ..compat import asyncio_run_forever, current_loop


class WSProxy:
    __slots__ = (
        'api_session', 'session_id',
        'app_name', 'protocol',
        'args', 'envs',
        'reader', 'writer',
        'down_task',
    )

    def __init__(self, api_session: AsyncSession,
                 session_id: str,
                 app_name: str,
                 protocol: str,
                 args: MutableMapping[str, str], 
                 envs: MutableMapping[str, str],
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        self.api_session = api_session
        self.session_id = session_id
        self.app_name = app_name
        self.protocol = protocol
        self.args = args
        self.envs = envs
        self.reader = reader
        self.writer = writer
        self.down_task = None

    async def run(self):
        path = "/stream/kernel/{0}/{1}proxy".format(self.session_id, self.protocol)
        params = {'app': self.app_name}

        if len(self.args.keys()) > 0:
            params['arguments'] = json.dumps(self.args)
        if len(self.envs.keys()) > 0:
            params['envs'] = json.dumps(self.envs)

        api_rqst = Request(
            self.api_session, "GET", path, b'',
            params=params,
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
                        try:
                            await self.writer.wait_closed()
                        except (BrokenPipeError, IOError):
                            # closed
                            pass

            self.down_task = asyncio.ensure_future(downstream())
            try:
                while True:
                    chunk = await self.reader.read(DEFAULT_CHUNK_SIZE)
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
        'args', 'envs',
        'api_session', 'local_server', 'loop',
    )

    def __init__(self, api_session, session_id, app_name,
                 protocol, host, port, args, envs, *, loop=None):
        self.api_session = api_session
        self.session_id = session_id
        self.app_name = app_name
        self.protocol = protocol
        self.host = host
        self.port = port
        self.args = args 
        self.envs = envs
        self.local_server = None
        self.loop = loop if loop else current_loop()

    async def handle_connection(self, reader, writer):
        p = WSProxy(self.api_session, self.session_id,
                    self.app_name, self.protocol,
                    self.args, self.envs,
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
@click.option('-p', '--protocol', type=click.Choice(['http', 'tcp']), default='http',
              help='The application-level protocol to use.')
@click.option('-b', '--bind', type=str, default='127.0.0.1:8080', metavar='[HOST:]PORT',
              help='The IP/host address and the port number to bind this proxy.')
@click.option('--arg', type=str, multiple=True, metavar='"--option <value>"', help='Add additional argument when starting service.')
@click.option('--env', type=str, multiple=True, metavar='"ENVNAME=envvalue"', help='Add additional environment variable when starting service.')
@click.option('--show-configurables', is_flag=True, 
              help='List available additional arguments and environment variables when starting service.')
def app(session_id, app, protocol, bind, arg, env, show_configurables):
    """
    Run a local proxy to a service provided by Backend.AI compute sessions.

    The type of proxy depends on the app definition: plain TCP or HTTP.

    \b
    SESSID: The compute session ID.
    APP: The name of service provided by the given session.
    """
    api_session = None
    runner = None

    async def print_arguments():
        nonlocal api_session
        api_session = AsyncSession()
        path = "/stream/kernel/{0}/apps".format(session_id)
        api_rqst = Request(
            api_session, "GET", path, b'',
            params={'app': app},
            content_type="application/json")
        try:
            async with api_rqst.fetch() as resp:
                data = await resp.json()
                if 'allowed_arguments' in data.keys():
                    print_info('Available arguments: {0}'.format(data['allowed_arguments']))
                if 'allowed_envs' in data.keys():
                    print_info('Available environment variables: {0}'.format(data['allowed_envs']))
            await api_session.close()
        except:
            pass

    if show_configurables:
        loop = current_loop()
        loop.run_until_complete(print_arguments())
        return 

    bind_parts = bind.rsplit(':', maxsplit=1)
    if len(bind_parts) == 1:
        host = '127.0.0.1'
        port = int(bind_parts[0])
    elif len(bind_parts) == 2:
        host = bind_parts[0]
        port = int(bind_parts[1])

    async def app_setup():
        nonlocal api_session, runner
        loop = current_loop()
        api_session = AsyncSession()
        arguments, envs = {}, {}
        if len(arg) > 0:
            for argline in arg:
                split = argline.strip().split(' ', maxsplit=2)
                if len(split) == 2:
                    arguments[split[0]] = split[1]
                else:
                    arguments[split[0]] = ''
        
        if len(env) > 0:
            for envline in env:
                split = envline.strip().split('=', maxsplit=2)
                if len(split) == 2:
                    envs[split[0]] = split[1]
                else:
                    envs[split[0]] = ''

        runner = ProxyRunner(api_session, session_id, app,
                             protocol, host, port,
                             arguments, envs,
                             loop=loop)
        await runner.ready()

        user_url_template = "{protocol}://{host}:{port}"
        path = "/stream/kernel/{0}/apps".format(session_id)
        api_rqst = Request(
            api_session, "GET", path, b'',
            params={'app': app},
            content_type="application/json")
        try:
            async with api_rqst.fetch() as resp:
                data = await resp.json()
                if 'url_template' in data.keys():
                    user_url_template = data['url_template']
        except:
            if app == 'vnc-web':
                user_url_template = \
                    "{protocol}://{host}:{port}/vnc.html" \
                    "?host={host}&port={port}&password=backendai&autoconnect=true"

        user_url = user_url_template.format(protocol=protocol, host=host, port=port)
        print_info(
            "A local proxy to the application \"{0}\" ".format(app) +
            "provided by the session \"{0}\" ".format(session_id) +
            "is available at:\n{0}".format(user_url)
        )
        if host == '0.0.0.0':
            print_warn('NOTE: Replace "0.0.0.0" with the actual hostname you use '
                       'to connect with the CLI app proxy.')

    async def app_shutdown():
        nonlocal api_session, runner
        print_info("Shutting down....")
        await runner.close()
        await api_session.close()
        print_info("The local proxy to \"{}\" has terminated."
                   .format(app))

    asyncio_run_forever(app_setup(), app_shutdown(),
                        stop_signals={signal.SIGINT, signal.SIGTERM})
