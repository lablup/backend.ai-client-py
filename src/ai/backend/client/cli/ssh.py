import subprocess
import click
from . import main


@main.command()
@click.argument("user", default="work", type=str, metavar='USER')
@click.argument("host", default="localhost", type=str, metavar='HOST')
@click.option('-i', '--id_path', default="~/.ssh/id_container",  type=str, metavar='ID',
              help="path to id_container, ex.) ~/.ssh/id_container")
@click.option('-p', '--port',  type=int, metavar='PORT', help="host port number")
def ssh(user, host, id_path, port):
    """SSH client to SSH server.

    \b
    USER: Name of the user at the session image. Default: work
    HOST: ip address of the host machine. Default: localhost or 127.0.0.1
    ID_PATH: path to the id_container which contains private key of the remote host.
    Default ~/.ssh/id_container
    PORT: port number of remote host SSH server.
    """

    ssh = subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", "-i", id_path,
                            "{}@{}".format(user, host),
                            "-p", str(port)], shell=False)
    ssh.communicate()
    print("done")
    return 1
