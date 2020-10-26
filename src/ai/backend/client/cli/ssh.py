import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='SESS_NAME')
@click.option('-p', '--port',  type=int, metavar='PORT', default=9922,
              help="the port number is for localhost")
def ssh(sess_name, port):
    """Execute the SSH client against the backend.ai SSH server.

    \b
    sess_name: name of backend.ai session executed buy user.
    """

    user = "work"
    host = "localhost"

    subprocess.run(["backend.ai", "download", "{}".format(sess_name),
                    "id_container"], shell=False)

    subprocess.run(["mv", "id_container", "~/.ssh/{}".format(sess_name)],
                   shell=False)

    subprocess.run(["backend.ai", "app", "{}".format(sess_name),
                    "sshd", "-b", "{}".format(port)], shell=True)

    try:
        ssh_proc = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no",
                                   "-i",
                                   "~/.ssh/{}".format(sess_name),
                                   "{}@{}".format(user, host),
                                   "-p", str(port)],  shell=False, check=True)
        try:
            subprocess.run(["rm", "-f", "~/.ssh/{}".format(sess_name)],
                           shell=False, check=True)
        except subprocess.CalledProcessError as e:
            return e.returncode
        return ssh_proc.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
