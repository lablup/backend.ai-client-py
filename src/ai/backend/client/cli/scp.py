import subprocess
import click
from . import main


@main.command()
@click.argument("sess_name",  type=str, metavar='SESS_NAME')
@click.argument("src",  type=str, metavar='SRC')
@click.argument("dest",  type=str, default="work@localhost", metavar='DEST')
@click.option('-p', '--port',  type=str, metavar='PORT', default=9922,
              help="the port number is for localhost")
@click.option('-r',  '--recursive', default=False, is_flag=True,
              help="recursive flag option to process directories")
def scp(sess_name, src, dest, port, recursive):
    """Execute the scp command against the target compute session

    \b
    First connection is made through `backend.ai ssh sess_name`
    which starts SSH Server.
    SESS_NAME: Name of the running session.
    SRC: file or directory which you want to move
    Dest: file or directory destination. Ex) work@localhost:tmp/

    Example usage: upload local directory to remote host:
    backend.ai scp mysess -p 9922 -r tmp/ work@localhost:tmp2/
    download directory from host to local:
    backend.ai scp mysess -p 9922 -r work@localhost:tmp2/ tmp/
    """

    opt_r = "-r" if recursive else ""

    try:
        scp_proc = subprocess.run(["scp", "-o", "StrictHostKeyChecking=no",
                                   "-i",
                                   "~/.ssh/{}".format(sess_name), "-P",
                                   str(port),
                                   opt_r, src, dest],
                                  shell=False, check=True)
        return scp_proc.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
