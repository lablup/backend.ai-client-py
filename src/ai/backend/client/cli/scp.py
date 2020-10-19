import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='USER')
@click.option('-p', '--port',  type=int, metavar='PORT', default=9922, help="host port number")
@click.option('-c', '--command', type=str, metavar="COMMAND", help="command to copy files")
def scp(sess_name, port, command):
    """SSH client to SSH server.

    \b
    USER: Name of the user at the session image. Default: work
    HOST: ip address of the host machine. Default: localhost or 127.0.0.1
    ID_PATH: path to the id_container which contains private key of the remote host.
    Default ~/.ssh/id_container
    PORT: port number of remote host SSH server.
    """
    id_path = "~/.ssh/id_container"
    user = "work"
    host = "localhost"

    popen = subprocess.Popen(["backend.ai", "download", "{}".format(sess_name),
                              "id_container"], shell=False)
    popen.communicate()
    popen = subprocess.Popen(["mv", "id_container", "~/.ssh/"], shell=False)
    popen.communicate()
    popen = subprocess.Popen(["backend.ai", "app", "{}".format(sess_name),
                              "sshd", "-b", "{}".format(port)], shell=True)
    popen.communicate()

    info_str = "session name: {}; user: {}; server: {}; port: {}".format(
                sess_name, user, host, port)
    popen = subprocess.Popen(["echo",
                             "\n****************\n{}\n****************"
                              .format(info_str)], shell=False)

    scp = subprocess.Popen(["scp", "-o", "StrictHostKeyChecking=no", "-i",
                            id_path, "-P", port, command], shell=False)
    scp.communicate()
    # scp -o StrictHostKeyChecking=no -i id_container -P 9922 vfolder.py work@localhost:tmp/
    print("Done")
    return 1
