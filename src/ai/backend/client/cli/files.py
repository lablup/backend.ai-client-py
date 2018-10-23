from datetime import datetime
import json
from pathlib import Path

from tabulate import tabulate

from . import register_command
from .pretty import print_wait, print_done, print_fail
from ..exceptions import BackendError
from ..session import Session


@register_command
def upload(args):
    """
    Upload files to user's home folder.
    """
    with Session() as session:
        try:
            print_wait('Uploading files...')
            kernel = session.Kernel(args.sess_id_or_alias)
            kernel.upload(args.files, show_progress=True)
            print_done('Uploaded.')
        except BackendError as e:
            print_fail(str(e))


upload.add_argument('sess_id_or_alias', metavar='NAME',
                    help=('The session ID or its alias given when creating the'
                          'session.'))
upload.add_argument('files', type=Path, nargs='+', help='File paths to upload.')


@register_command
def download(args):
    """
    Download files from a running container.
    """
    with Session() as session:
        try:
            print_wait('Downloading file(s) from {}...'
                       .format(args.sess_id_or_alias))
            kernel = session.Kernel(args.sess_id_or_alias)
            kernel.download(args.files, args.dest, show_progress=True)
            print_done('Downloaded to {}.'.format(args.dest.resolve()))
        except BackendError as e:
            print_fail(str(e))


download.add_argument('sess_id_or_alias', metavar='NAME',
                      help=('The session ID or its alias given when creating the'
                            'session.'))
download.add_argument('files', nargs='+',
                      help='File paths inside container')
download.add_argument('--dest', type=Path, default='.',
                      help='Destination path to store downloaded file(s)')


@register_command
def ls(args):
    """
    List files in a path of a running container.
    """
    with Session() as session:
        try:
            print_wait('Retrieving list of files in "{}"...'.format(args.path))
            kernel = session.Kernel(args.sess_id_or_alias)
            result = kernel.list_files(args.path)

            if 'errors' in result and result['errors']:
                print_fail(result['errors'])
                return

            files = json.loads(result['files'])
            table = []
            headers = ['file name', 'size', 'modified', 'mode']
            for file in files:
                mdt = datetime.fromtimestamp(file['mtime'])
                mtime = mdt.strftime('%b %d %Y %H:%M:%S')
                row = [file['filename'], file['size'], mtime, file['mode']]
                table.append(row)
            print_done('Retrived.')
            print('Path in container:', result['abspath'], end='')
            print(tabulate(table, headers=headers))
        except BackendError as e:
            print_fail(str(e))


ls.add_argument('sess_id_or_alias', metavar='SESSID',
                help='The session ID or its alias given when creating the session.')
ls.add_argument('path', metavar='PATH', nargs='?', default='/home/work',
                help='Path inside container')
