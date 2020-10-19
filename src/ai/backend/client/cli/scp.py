import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='SESS_NAME')
@click.argument("src",  type=str, metavar='SRC')
@click.argument("dest",  type=str, default="work@localhost", metavar='DEST')
@click.option('-p', '--port',  type=str, metavar='PORT', default=9922,
              help="host port number")
@click.option('-r', '--reverse',  metavar='REVERSE', default=False, is_flag=True,
              help="option to reverse copy from server to local")
def scp(sess_name, src, dest, port, reverse):
    """SCP client to Backend.AI SSH server.

    \b
    It is assumed that first connection is made through backend.ai ssh which
     starts SSH Server.

    SESS_NAME: Name of the running session.
    SRC: file which you want to move
    Dest: ip address of the host machine and directory. work@localhost:tmp/
    Port: Port num where ssh is opened
    Reverse: Flag to download file from server to directory

    Full example to download file: backend.ai mysess  vfolder.py work@localhost:tmp/ -p 9922 -r
    """

    id_path = "~/.ssh/id_container"

    info_str = "session name: {}; src: {}; dest: {}; port: {}".format(
                sess_name, src, dest, port)

    subprocess.Popen(["echo",
                      "\n****************\n{}; \n****************"
                      .format(info_str)], shell=False)

    if not reverse:
        scp_proc = subprocess.Popen(["scp", "-o", "StrictHostKeyChecking=no", "-i",
                                    id_path, "-P", str(port), src, dest],
                                    shell=False)
    else:
        scp_proc = subprocess.Popen(["scp", "-o", "StrictHostKeyChecking=no", "-i",
                                     id_path, "-P", str(port), dest, src],
                                    shell=False)
    scp_proc.communicate()
    print("Done")
    return 1
