import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='SESS_NAME')
@click.option('-p', '--port',  type=int, metavar='PORT', default=9922, help="host port number")
def ssh(sess_name, port):
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

    popen = subprocess.Popen(["backend.ai", "download", "{}".format(sess_name), "id_container"], shell=False)
    popen.communicate()
    popen = subprocess.Popen(["mv", "id_container", "~/.ssh/"], shell=False)
    popen.communicate()
    popen = subprocess.Popen(["backend.ai", "app", "{}".format(sess_name), "sshd", "-b", "{}".format(port)], shell=True)
    popen.communicate()

    info_str = "session name: {}; user: {}; server: {}; port: {}".format(sess_name, user, host, port)
    popen = subprocess.Popen(["echo", "\n****************\n{}\n****************".format(info_str)], shell=False)
    popen.communicate()

    ssh_proc = subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", "-i", id_path,
                            "{}@{}".format(user, host),
                            "-p", str(port)], shell=False)
    ssh_proc.communicate()
    print("Goodbye")
    return 1
