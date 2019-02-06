from datetime import datetime
import json
from pathlib import Path
import sys

import click
from tabulate import tabulate

from . import AliasGroup, main
from ..config import get_config
from .pretty import print_wait, print_done, print_error, print_fail
from ..session import Session


@main.group(cls=AliasGroup)
def vfolder():
    '''Provides virtual folder operations.'''


@vfolder.command()
def list():
    '''List virtual folders that belongs to the current user.'''
    fields = [
        ('Name', 'name'),
        ('ID', 'id'),
        ('Owner', 'is_owner'),
        ('Permission', 'permission'),
    ]
    with Session() as session:
        try:
            resp = session.VFolder.list()
            if not resp:
                print('There is no virtual folders created yet.')
                return
            rows = (tuple(vf[key] for _, key in fields) for vf in resp)
            hdrs = (display_name for display_name, _ in fields)
            print(tabulate(rows, hdrs))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('host', type=str, default=None)
def create(name, host):
    '''Create a new virtual folder.

    \b
    NAME: Name of a virtual folder.
    HOST: Name of a virtual folder host in which the virtual folder will be created.
    '''
    with Session() as session:
        try:
            result = session.VFolder.create(name, host)
            print('Virtual folder "{0}" is created.'.format(result['name']))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
def delete(name):
    '''Delete the given virtual folder. This operation is irreversible!

    NAME: Name of a virtual folder.
    '''
    with Session() as session:
        try:
            session.VFolder(name).delete()
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
def info(name):
    '''Show the information of the given virtual folder.

    NAME: Name of a virtual folder.
    '''
    with Session() as session:
        try:
            result = session.VFolder(name).info()
            print('Virtual folder "{0}" (ID: {1})'
                  .format(result['name'], result['id']))
            print('- Owner:', result['is_owner'])
            print('- Permission:', result['permission'])
            print('- Number of files: {0}'.format(result['numFiles']))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('filenames', type=Path, nargs=-1)
def upload(name, filenames):
    '''
    Upload a file to the virtual folder from the current working directory.
    The files with the same names will be overwirtten.

    \b
    NAME: Name of a virtual folder.
    FILENAMES: Paths of the files to be uploaded.
    '''
    with Session() as session:
        try:
            session.VFolder(name).upload(filenames, show_progress=True)
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('filenames', type=Path, nargs=-1)
def download(name, filenames):
    '''
    Download a file from the virtual folder to the current working directory.
    The files with the same names will be overwirtten.

    \b
    NAME: Name of a virtual folder.
    FILENAMES: Paths of the files to be uploaded.
    '''
    with Session() as session:
        try:
            session.VFolder(name).download(filenames, show_progress=True)
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('filenames', nargs=-1)
def cp(filenames):
    '''An scp-like shortcut for download/upload commands.

    FILENAMES: Paths of the files to operate on. The last one is the target while all
               others are the sources.  Either source paths or the target path should
               be prefixed with "<vfolder-name>:" like when using the Linux scp
               command to indicate if it is a remote path.
    '''
    raise NotImplementedError


@vfolder.command()
@click.argument('name', type=str)
@click.argument('path', type=str)
def mkdir(name, path):
    '''Create an empty directory in the virtual folder.

    \b
    NAME: Name of a virtual folder.
    PATH: The name or path of directory. Parent directories are created automatically
          if they do not exist.
    '''
    with Session() as session:
        try:
            session.VFolder(name).mkdir(path)
            print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command(aliases=['delete-file'])
@click.argument('name', type=str)
@click.argument('filenames', nargs=-1)
@click.option('-r', '--recursive', is_flag=True,
              help='Enable recursive deletion of directories.')
def rm(name, filenames, recursive):
    '''
    Delete files in a virtual folder.
    If one of the given paths is a directory and the recursive option is enabled,
    all its content and the directory itself are recursively deleted.

    This operation is irreversible!

    \b
    NAME: Name of a virtual folder.
    FILENAMES: Paths of the files to delete.
    '''
    with Session() as session:
        try:
            if input("> Are you sure? (y/n): ").lower().strip()[:1] == 'y':
                session.VFolder(name).delete_files(
                    filenames,
                    recursive=recursive)
                print_done('Done.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('path', metavar='PATH', nargs=1, default='.')
def ls(name, path):
    """
    List files in a path of a virtual folder.

    \b
    NAME: Name of a virtual folder.
    PATH: Path inside vfolder.
    """
    with Session() as session:
        try:
            print_wait('Retrieving list of files in "{}"...'.format(path))
            result = session.VFolder(name).list_files(path)
            if 'error_msg' in result and result['error_msg']:
                print_fail(result['error_msg'])
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
            print(tabulate(table, headers=headers))
        except Exception as e:
            print_error(e)


@vfolder.command()
@click.argument('name', type=str)
@click.argument('emails', type=str, nargs=-1, required=True)
@click.option('-p', '--perm', metavar='PERMISSION', type=str, default='rw',
              help='Permission to give. "ro" (read-only) / "rw" (read-write).')
def invite(name, emails, perm):
    """Invite other users to access the virtual folder.

    \b
    NAME: Name of a virtual folder.
    EMAIL: Emails to invite.
    """
    with Session() as session:
        try:
            assert perm in ['rw', 'ro'], \
                   'Invalid permission: {}'.format(perm)
            result = session.VFolder(name).invite(perm, emails)
            invited_ids = result.get('invited_ids', [])
            if len(invited_ids) > 0:
                print('Invitation sent to:')
                for invitee in invited_ids:
                    print('\t- ' + invitee)
            else:
                print('No users found. Invitation was not sent.')
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
def invitations():
    """List and manage received invitations.
    """
    with Session() as session:
        try:
            result = session.VFolder.invitations()
            invitations = result.get('invitations', [])
            if len(invitations) < 1:
                print('No invitations.')
                return
            print('List of invitations (inviter, vfolder id, permission):')
            for cnt, inv in enumerate(invitations):
                if inv['perm'] == 'rw':
                    perm = 'read-write'
                elif inv['perm'] == 'ro':
                    perm = 'read-only'
                else:
                    perm = inv['perm']
                print('[{}] {}, {}, {}'.format(cnt + 1, inv['inviter'],
                                               inv['vfolder_id'], perm))

            selection = input('Choose invitation number to manage: ')
            if selection.isdigit():
                selection = int(selection) - 1
            else:
                return
            if 0 <= selection < len(invitations):
                while True:
                    action = input('Choose action. (a)ccept, (r)eject, (c)ancel: ')
                    if action.lower() == 'a':
                        # TODO: Let user can select access_key among many.
                        #       Currently, the config objects holds only one key.
                        config = get_config()
                        result = session.VFolder.accept_invitation(
                            invitations[selection]['id'], config.access_key)
                        print(result['msg'])
                        break
                    elif action.lower() == 'r':
                        result = session.VFolder.delete_invitation(
                            invitations[selection]['id'])
                        print(result['msg'])
                        break
                    elif action.lower() == 'c':
                        break
        except Exception as e:
            print_error(e)
            sys.exit(1)
