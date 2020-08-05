from pathlib import Path
from unittest import mock


import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import Session
from ai.backend.client.test_utils import AsyncMock


def build_url(config, path: str):
    base_url = config.endpoint.path.rstrip('/')
    query_path = path.lstrip('/') if len(path) > 0 else ''
    path = '{0}/{1}'.format(base_url, query_path)
    canonical_url = config.endpoint.with_path(path)
    return canonical_url


@pytest.fixture(scope='module', autouse=True)
def api_version():
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch('ai.backend.client.session._negotiate_api_version', mock_nego_func):
        yield


def test_create_vfolder():
    with Session() as session, aioresponses() as m:
        payload = {
            'id': 'fake-vfolder-id',
            'name': 'fake-vfolder-name',
            'host': 'local',
        }
        m.post(build_url(session.config, '/folders'), status=201,
               payload=payload)
        resp = session.VFolder.create('fake-vfolder-name')
        assert resp == payload


def test_create_vfolder_in_other_host():
    with Session() as session, aioresponses() as m:
        payload = {
            'id': 'fake-vfolder-id',
            'name': 'fake-vfolder-name',
            'host': 'fake-vfolder-host',
        }
        m.post(build_url(session.config, '/folders'), status=201,
               payload=payload)
        resp = session.VFolder.create('fake-vfolder-name', 'fake-vfolder-host')
        assert resp == payload


def test_list_vfolders():
    with Session() as session, aioresponses() as m:
        payload = [
            {
                'name': 'fake-vfolder1',
                'id': 'fake-vfolder1-id',
                'host': 'fake-vfolder1-host',
                'is_owner': True,
                'permissions': 'wd',
            },
            {
                'name': 'fake-vfolder2',
                'id': 'fake-vfolder2-id',
                'host': 'fake-vfolder2-host',
                'is_owner': True,
                'permissions': 'wd',
            }
        ]
        m.get(build_url(session.config, '/folders'), status=200,
              payload=payload)
        resp = session.VFolder.list()
        assert resp == payload


def test_delete_vfolder():
    with Session() as session, aioresponses() as m:
        vfolder_name = 'fake-vfolder-name'
        m.delete(build_url(session.config, '/folders/{}'.format(vfolder_name)),
                 status=204)
        resp = session.VFolder(vfolder_name).delete()
        assert resp == {}


def test_vfolder_get_info():
    with Session() as session, aioresponses() as m:
        vfolder_name = 'fake-vfolder-name'
        payload = {
            'name': vfolder_name,
            'id': 'fake-vfolder-id',
            'host': 'fake-vfolder-host',
            'numFiles': 5,
            'created': '2018-06-02 09:04:15.585917+00:00',
            'is_owner': True,
            'permission': 'wd',
        }
        m.get(build_url(session.config, '/folders/{}'.format(vfolder_name)),
              status=200, payload=payload)
        resp = session.VFolder(vfolder_name).info()
        assert resp == payload


def test_vfolder_upload(tmp_path: Path):
    with Session() as session:
        tmp_path = Path().cwd()
        mock_file = 'test_request.py'  # example.bin
        #  mock_file.write_bytes(secrets.token_bytes(32))
        vfolder_name = 'mydata1'
        """
        m.post(build_url(session.config,
                         '/folders/{}/upload'.format(vfolder_name)),
               status=201)
        """
        resp = session.VFolder(vfolder_name).upload([mock_file],
                                                    basedir=tmp_path)
        assert resp == ''


def test_vfolder_delete_files():
    with Session() as session, aioresponses() as m:
        vfolder_name = 'fake-vfolder-name'
        files = ['fake-file1', 'fake-file2']
        m.delete(build_url(session.config,
                           '/folders/{}/delete_files'.format(vfolder_name)),
                 status=200, payload={})
        resp = session.VFolder(vfolder_name).delete_files(files)
        assert resp == '{}'


def test_vfolder_download(mocker):
    mock_reader = AsyncMock()
    mock_from_response = mocker.patch(
        'ai.backend.client.func.vfolder.aiohttp.MultipartReader.from_response',
        return_value=mock_reader)
    mock_reader.next = AsyncMock()
    mock_reader.next.return_value = None
    with Session() as session, aioresponses() as m:
        vfolder_name = 'fake-vfolder-name'
        m.get(build_url(session.config,
                        '/folders/{}/download'.format(vfolder_name)),
              status=200,
              headers={'X-TOTAL-PAYLOADS-LENGTH': '0'}, body='')
        session.VFolder(vfolder_name).download(['fake-file1'])
        assert mock_from_response.called == 1
        assert mock_reader.next.called == 1


def test_vfolder_list_files():
    with Session() as session, aioresponses() as m:
        vfolder_name = 'fake-vfolder-name'
        payload = {
            "files": [
                {
                    "mode": "-rw-r--r--",
                    "size": 4751244,
                    "ctime": 1528277299.2744732,
                    "mtime": 1528277299.2744732,
                    "atime": 1528277300.7658687,
                    "filename": "bigtxt.txt",
                },
                {
                    "mode": "-rw-r--r--",
                    "size": 200000,
                    "ctime": 1528333257.6576185,
                    "mtime": 1528288069.625786,
                    "atime": 1528332829.692922,
                    "filename": "200000",
                }
            ],
            "folder_path": "/mnt/local/1f6bd27fde1248cabfb50306ea83fc0a",
        }
        m.get(build_url(session.config,
                        '/folders/{}/files'.format(vfolder_name)),
              status=200, payload=payload)
        resp = session.VFolder(vfolder_name).list_files('.')
        assert resp == payload


def test_vfolder_invite():
    with Session() as session, aioresponses() as m:
        vfolder_name = 'fake-vfolder-name'
        user_ids = ['user1@lablup.com', 'user2@lablup.com']
        payload = {'invited_ids': user_ids}
        m.post(build_url(session.config,
                         '/folders/{}/invite'.format(vfolder_name)),
               status=201, payload=payload)
        resp = session.VFolder(vfolder_name).invite('rw', user_ids)
        assert resp == payload


def test_vfolder_invitations():
    with Session() as session, aioresponses() as m:
        payload = {
            'invitations': [
                {
                    'id': 'fake-invitation-id',
                    'inviter': 'inviter@lablup.com',
                    'perm': 'ro',
                    'vfolder_id': 'fake-vfolder-id',
                }
            ]
        }
        m.get(build_url(session.config, '/folders/invitations/list'),
              status=200, payload=payload)
        resp = session.VFolder.invitations()
        assert resp == payload


def test_vfolder_accept_invitation():
    with Session() as session, aioresponses() as m:
        payload = {
            'msg': ('User invitee@lablup.com now can access'
                    ' vfolder fake-vfolder-id'),
        }
        m.post(build_url(session.config, '/folders/invitations/accept'),
               status=200, payload=payload)
        resp = session.VFolder.accept_invitation('inv-id')
        assert resp == payload


def test_vfolder_delete_invitation():
    with Session() as session, aioresponses() as m:
        payload = {'msg': 'Vfolder invitation is deleted: fake-inv-id.'}
        m.delete(build_url(session.config, '/folders/invitations/delete'),
                 status=200, payload=payload)
        resp = session.VFolder.delete_invitation('inv-id')
        assert resp == payload
