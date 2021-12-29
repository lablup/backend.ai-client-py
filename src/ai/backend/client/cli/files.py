from datetime import datetime
import json
from pathlib import Path
import sys

import click
from humanize import naturalsize
from tabulate import tabulate

from . import main
from .pretty import print_wait, print_done, print_error, print_fail, print_warn
from ..session import Session


@main.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('files', type=click.Path(exists=True), nargs=-1)
def upload(session_id, files):
    """
    Upload files to user's home folder.

    \b
    SESSID: Session ID or its alias given when creating the session.
    FILES: Path to upload.
    """
    if len(files) < 1:
        print_warn("Please specify one or more file paths after session ID or name.")
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


@main.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('files', nargs=-1)
@click.option('--dest', type=Path, default='.',
              help='Destination path to store downloaded file(s)')
def download(session_id, files, dest):
    """
    Download files from a running container.

    \b
    SESSID: Session ID or its alias given when creating the session.
    FILES: Paths inside container.
    """
    if len(files) < 1:
        print_warn("Please specify one or more file paths after session ID or name.")
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


@main.command()
@click.argument('session_id', metavar='SESSID')
@click.argument('path', metavar='PATH', nargs=1, default='/home/work')
def ls(session_id, path):
    """
    List files in a path of a running container.

    \b
    SESSID: Session ID or its alias given when creating the session.
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
