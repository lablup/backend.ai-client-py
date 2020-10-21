import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='SESS_NAME')
@click.option('-p', '--port',  type=int, metavar='PORT', default=9922,
              help="the port number is for localhost")
def ssh(sess_name, port):
    """SSH client to SSH server.

    \b
    USER: Name of the user at the session image. Default: work
    HOST: ip address of the host machine. Default: localhost or 127.0.0.1
    ID_PATH: path to the id_container which contains private key of the remote host.
    Default ~/.ssh/id_container
    PORT: port number of remote host SSH server.
    """

    user = "work"
    host = "localhost"

    subprocess.run(["backend.ai", "download", "{}".format(sess_name),
                    "id_container"], shell=False)

    subprocess.run(["mv", "id_container", "~./ssh/{}".format(sess_name)],
                   shell=False)

    subprocess.run(["backend.ai", "app", "{}".format(sess_name),
                    "sshd", "-b", "{}".format(port)], shell=True)

    info_str = "session name: {}; user: {}; server: {}; port: {}".format(
                sess_name, user, host, port)

    print("\n****************\n{}; \n****************".format(info_str))

    ssh_proc = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-i",
                               "~/.ssh/{}".format(sess_name),
                               "{}@{}".format(user, host),
                               "-p", str(port)], shell=False)
    if ssh_proc:
        subprocess.run(["rm", "-f", "~/.ssh/{}".format(sess_name)],
                       shell=False)
        click.Abort()
        return ssh_proc
    else:
        subprocess.run(["rm", "-f", "~/.ssh/{}".format(sess_name)],
                       shell=False)
        return ssh_proc
