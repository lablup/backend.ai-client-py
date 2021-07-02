from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

import click
from humanize import naturalsize
from tabulate import tabulate

from .main import main
from .pretty import print_wait, print_done, print_error, print_fail
from .ssh import container_ssh_ctx
from ..session import Session


@main.group()
def session():
    '''Provides compute session operations'''


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('files', type=click.Path(exists=True), nargs=-1)
def upload(session_id, files):
    """
    Upload the given files to the target compute session's home directory.
    If the target directory is in a storage folder mount, the operation is
    effectively same to uploading files to the storage folder.
    It is recommended to use storage folder commands for large file transfers
    to utilize the storage proxy.

    For cluster sessions, the files are only uploaded to the main container.

    \b
    SESSID: Session ID or name.
    FILES: One or more paths to upload.
    """
    if len(files) < 1:
        return
    with Session() as session:
        try:
            print_wait('Uploading files...')
            kernel = session.ComputeSession(session_id)
            kernel.upload(files, show_progress=True)
            print_done('Uploaded.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('files', nargs=-1)
@click.option('--dest', type=Path, default='.',
              help='Destination path to store downloaded file(s)')
def download(session_id, files, dest):
    """
    Download files from a running compute session.
    If the source path is in a storage folder mount, the operation is
    effectively same to downloading files from the storage folder.
    It is recommended to use storage folder commands for large file transfers
    to utilize the storage proxy.

    For cluster sessions, the files are only downloaded from the main container.

    \b
    SESSID: Session ID or name.
    FILES: One or more paths inside compute session.
    """
    if len(files) < 1:
        return
    with Session() as session:
        try:
            print_wait('Downloading file(s) from {}...'
                       .format(session_id))
            kernel = session.ComputeSession(session_id)
            kernel.download(files, dest, show_progress=True)
            print_done('Downloaded to {}.'.format(dest.resolve()))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('path', metavar='PATH', nargs=1, default='/home/work')
def ls(session_id, path):
    """
    List files in a path of a running compute session.

    For cluster sessions, it lists the files of the main container.

    \b
    SESSID: Session ID or name.
    PATH: Path inside container.
    """
    with Session() as session:
        try:
            print_wait('Retrieving list of files in "{}"...'.format(path))
            kernel = session.ComputeSession(session_id)
            result = kernel.list_files(path)

            if 'errors' in result and result['errors']:
                print_fail(result['errors'])
                sys.exit(1)

            files = json.loads(result['files'])
            table = []
            headers = ['File name', 'Size', 'Modified', 'Mode']
            for file in files:
                mdt = datetime.fromtimestamp(file['mtime'])
                fsize = naturalsize(file['size'], binary=True)
                mtime = mdt.strftime('%b %d %Y %H:%M:%S')
                row = [file['filename'], fsize, mtime, file['mode']]
                table.append(row)
            print_done('Retrived.')
            print(tabulate(table, headers=headers))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@session.command()
@click.argument('session_id', metavar='SESSID')
def logs(session_id):
    '''
    Shows the full console log of a compute session.

    \b
    SESSID: Session ID or its alias given when creating the session.
    '''
    with Session() as session:
        try:
            print_wait('Retrieving live container logs...')
            kernel = session.ComputeSession(session_id)
            result = kernel.get_logs().get('result')
            logs = result.get('logs') if 'logs' in result else ''
            print(logs)
            print_done('End of logs.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


def _ssh_cmd(docs: str = None):

    @click.argument("session_ref",  type=str, metavar='SESSION_REF')
    @click.option('-p', '--port',  type=int, metavar='PORT', default=9922,
                  help="the port number for localhost")
    @click.pass_context
    def ssh(ctx: click.Context, session_ref: str, port: int) -> None:
        """Execute the ssh command against the target compute session

        \b
        SESSION_REF: The user-provided name or the unique ID of a running compute session.

        All remaining options and arguments not listed here are passed to the ssh command as-is.
        """
        try:
            with container_ssh_ctx(session_ref, port) as key_path:
                ssh_proc = subprocess.run(
                    [
                        "ssh",
                        "-o", "StrictHostKeyChecking=no",
                        "-i", key_path,
                        "work@localhost",
                        "-p", str(port),
                        *ctx.args,
                    ],
                    shell=False,
                    check=False,  # be transparent against the main command
                )
                sys.exit(ssh_proc.returncode)
        except Exception as e:
            print_error(e)

    if docs is not None:
        ssh.__doc__ = docs
    return ssh


_ssh_cmd_context_settings = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
    "allow_interspersed_args": True,
}

# Make it available as:
# - backend.ai ssh
# - backend.ai session ssh
main.command(
    context_settings=_ssh_cmd_context_settings,
)(_ssh_cmd(docs="Alias of \"session ssh\""))
ssh = session.command(
    context_settings=_ssh_cmd_context_settings,
)(_ssh_cmd())


def _scp_cmd(docs: str = None):

    @click.argument("session_ref", type=str, metavar='SESSION_REF')
    @click.argument("src", type=str, metavar='SRC')
    @click.argument("dst", type=str, metavar='DST')
    @click.option('-p', '--port',  type=str, metavar='PORT', default=9922,
                  help="the port number for localhost")
    @click.option('-r',  '--recursive', default=False, is_flag=True,
                  help="recursive flag option to process directories")
    @click.pass_context
    def scp(
        ctx: click.Context,
        session_ref: str,
        src: str,
        dst: str,
        port: int,
        recursive: bool,
    ) -> None:
        """Execute the scp command against the target compute session

        \b
        The SRC and DST have the same format with the original scp command,
        either a remote path as "work@localhost:path" or a local path.

        SESSION_REF: The user-provided name or the unique ID of a running compute session.
        SRC: the source path
        DST: the destination path

        All remaining options and arguments not listed here are passed to the ssh command as-is.

        Examples:

        * Uploading a local directory to the session:

          > backend.ai scp mysess -p 9922 -r tmp/ work@localhost:tmp2/

        * Downloading a directory from the session:

          > backend.ai scp mysess -p 9922 -r work@localhost:tmp2/ tmp/
        """
        recursive_args = []
        if recursive:
            recursive_args.append("-r")
        try:
            with container_ssh_ctx(session_ref, port) as key_path:
                scp_proc = subprocess.run(
                    [
                        "scp",
                        "-o", "StrictHostKeyChecking=no",
                        "-i", key_path,
                        "-P", str(port),
                        *recursive_args,
                        src, dst,
                        *ctx.args,
                    ],
                    shell=False,
                    check=False,  # be transparent against the main command
                )
                sys.exit(scp_proc.returncode)
        except Exception as e:
            print_error(e)

    if docs is not None:
        scp.__doc__ = docs
    return scp


# Make it available as:
# - backend.ai scp
# - backend.ai session scp
main.command(
    context_settings=_ssh_cmd_context_settings,
)(_scp_cmd(docs="Alias of \"session scp\""))
scp = session.command(
    context_settings=_ssh_cmd_context_settings,
)(_scp_cmd())
