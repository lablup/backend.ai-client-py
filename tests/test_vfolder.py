from pathlib import Path
from unittest import mock

import secrets
import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import Session, AsyncSession
from ai.backend.client.test_utils import AsyncMock
from ai.backend.client.request import Request, Response


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


@pytest.mark.asyncio
async def test_upload_jwt_generation(tmp_path):
    with aioresponses() as m:

        async with AsyncSession() as session:
            mock_file = tmp_path / 'example.bin'
            mock_file.write_bytes(secrets.token_bytes(32))

            vfolder_name = 'fake-vfolder-name'

            file_size = '1024'
            payload = {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9. \
            eyJwYXRoIjoiaHR0cDoxMjcuMC4wLjEvZm9sZGVycy9mYWtlLXZmb2xkZXItbmFtZS9yZXF1ZXN0LXVwbG9hZCIsInNpemUiOjEwMjR9.\
            5IXk0xdrr6aPzVjud4cdfcXWch7Bq-m7SlFhnUv8XL8'}

            m.post(build_url(session.config, '/folders/{}/request-upload'.format(vfolder_name)),
                   headers={'path': "{}".format(str(Path(tmp_path / 'example.bin'))),
                            'size': file_size,
                            'Host': '127.0.0.1:8081',
                            'User-Agent':
                            'Backend.AI Client for Python 20.09.0a1.dev0',
                            'X-BackendAI-Domain': 'default',
                            'X-BackendAI-Version': 'v6.20200815',
                            'Date': '2020-08-31T07:33:25.897405+00:00',
                            'Content-Type': 'application/json',
                            'Authorization': 'BackendAI signMethod=HMAC-SHA256,\
                            credential=AKIAIOSFODNN7EXAMPLE: \
                            8b984a9b85a1e6ba0b7368a1dc41232a \
                            fee0981b471c190ab6dca95601365354',
                            'Accept': '*/*',
                            'Accept-Encoding': 'gzip, deflate',
                            'Content-Length': '1024'},
                   payload=payload, status=200)

            rqst = Request(session, 'POST', '/folders/{}/request-upload'.format(vfolder_name))
            rqst.set_json({
                'path': "{}".format(str(Path(mock_file))),
                'size': str(file_size),
            })

            async with rqst.fetch() as resp:
                res = await resp.json()
                assert isinstance(resp, Response)
                assert resp.status == 200
                assert resp.content_type == 'application/json'
                assert res == payload
                assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' in res['token']


def test_vfolder_upload(tmp_path: Path):
    with Session() as session, aioresponses() as m:

        mock_file = tmp_path / 'example.bin'
        mock_file.write_bytes(secrets.token_bytes(1024))

        vfolder_name = 'fake-vfolder-name'
        m.post(build_url(session.config, '/folders/{}/upload'.format(vfolder_name)),
               status=201)
        # Note: aioresponses ignores the query parameters
        m.post(build_url(session.config, '/folder/file/upload'), status=200)
        m.patch(build_url(session.config, '/folder/file/upload'), status=204)
        m.head(build_url(session.config, '/folder/file/upload'), status=200)

        resp = session.VFolder(vfolder_name).upload([mock_file], basedir=tmp_path)
        assert resp == ""


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
        # client to manager
        m.get(
            build_url(session.config,
                      'session/{}/download'.format(vfolder_name)),
            status=200,
            headers={
                'Host': 'local',
                'User-Agent': 'Backend.AI Client for Python 20.09.0a1.dev0',
                'X-BackendAI-Domain': 'default',
                'X-BackendAI-Version': 'v6.20200815',
                'Date': '2020-08-31T00:00:00.000000+00:00',
                'Content-Type': 'application/json',
                'Authorization': 'BackendAI signMethod=HMAC-SHA256, \
                credential=AKIAIOSFODNN7EXAMPLE: \
                26ff062d498962fbfb1879f8bc448d3e5757fdd7ea4df0ba56b81e0334237304',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Length': '21'},
            body='',
        )

        # manager to storage-proxy
        m.post(build_url(session.config,
               '/folder/{}/download'.format(vfolder_name)),
               status=200,
               headers={"X-TOTAL-PAYLOADS-LENGTH": 0})

        m.get(build_url(session.config, '/folder/{}/download'.format(vfolder_name)),
              status=200)

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
