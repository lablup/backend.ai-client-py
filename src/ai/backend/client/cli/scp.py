import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='SESS_NAME')
@click.argument("src",  type=str, metavar='SRC')
@click.argument("dest",  type=str, default="work@localhost", metavar='DEST')
@click.option('-p', '--port',  type=str, metavar='PORT', default=9922,
              help="the port number is for localhost")
@click.option('-r',  metavar="RECURSIVE", default=False, is_flag=True,
              help="recursive option to process directories")
def scp(sess_name, src, dest, port, r):
    """SCP client to Backend.AI SSH server.

    \b
    It is assumed that first connection is made through `backend.ai ssh sess_name`
    which starts SSH Server.
    SESS_NAME: Name of the running session.
    SRC: file or directory which you want to move
    Dest: file or directory destination. Ex) work@localhost:tmp/
    Port: Port num where ssh is opened
    R: Option to download/ upload directories

    Example: upload local directory to remote host:
    backend.ai scp mysess -p 9922 -r tmp/ work@localhost:tmp2/
    download directory from host to local:
    backend.ai scp mysess -p 9922 -r work@localhost:tmp2/ tmp/
    """

    info_str = "session name: {}; src: {}; dest: {}; port: {}".format(
                sess_name, src, dest, port)

    print("\n****************\n{}; \n****************".format(info_str))
    opt_r = "-r" if r else ""
    scp_proc = subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-i",
                               "~/.ssh/{}".format(sess_name), "-P", str(port),
                               opt_r, src, dest],
                               shell=False)

    if scp_proc:
        click.Abort()
        return scp_proc
    else:
        return scp_proc
