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


@pytest.mark.skip
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
                   payload=payload, status=200)

            """
            Since requests send paramers url should contain params inorder to get JWT token
            m.post(build_url(session.config, '/folders/{}/request-upload?path={}&size={}' \
            .format(vfolder_name, str(Path(mock_file)), str(file_size))),
                   payload=payload, status=200)
            """
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


@pytest.mark.skip(reason="postponed test implementation")
@pytest.mark.asyncio
async def test_vfolder_upload(tmp_path: Path):
    mock_file = tmp_path / 'example.bin'
    mock_file.write_bytes(secrets.token_bytes(1024))

    with aioresponses() as m:

        async with AsyncSession() as session:
            vfolder_name = 'fake-vfolder-name'

            storage_path = str(build_url(session.config, 'folder/{}/upload'
                                .format(vfolder_name))).replace('8081', '6021')
            storage_path2 = str(build_url(session.config, '/upload')).replace('8081', '6021')

            payload = {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9. \
            eyJwYXRoIjoiaHR0cDoxMjcuMC4wLjEvZm9sZGVycy9mYWtlLXZmb2xkZXItbmFtZS9yZXF1ZXN0LXVwbG9hZCIsInNpemUiOjEwMjR9.\
            5IXk0xdrr6aPzVjud4cdfcXWch7Bq-m7SlFhnUv8XL8', 'url': storage_path}
            storage_payload = {'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9. \
                eyJvcCI6InVwbG9hZCIsInZvbHVtZSI6InZvbHVtZTEiLCJ2ZmlkIjoiO \
                DBiYWYyYjgtNTY3My00MmVkLTgyZWEtYj \
                NmNzNmOWQwNjAzIiwicmVscGF0aCI6InNldHVwLmNmZyIsInNpemUiOjU \
                yNywic2Vzc2lvbiI6ImE3YzZiY2I1MWRlY2I3NzJjZjRkMDI3YjA5 \
                MGI5NGM5IiwiZXhwIjoxNTk5MTIzMzYxfQ. \
                D13UMFrz-2qq9c0k4MGpjVOMn5Z9-fyR5tRRIkvtvqk'}

            """
            # 0. This works and passes test when reqeusting jwt in test_upload_jwt_generation().
            # but here it freezes the client
            """

            m.post(build_url(session.config, '/folders/{}/request-upload'.format(vfolder_name)),
                             payload=payload, status=200)
            # 1. Client to Manager throught Request
            m.post(build_url(session.config, "/folders/{}/request-upload?path='{}'&size={}".format(
                             vfolder_name, mock_file, 1024)), payload=payload['token'], status=200)

            # 2. Response from storage to manager
            m.post(storage_path + "?volume= \
                   volume1&vfid=80baf2b8-5673-42ed-82ea-b3f73f9d0603&relpath={}&size={}"
                   .format('example.bin', '1024'),
                   payload=payload,
                   status=200)

            # 3. Client to Manager through TusClient. Upload url

            tus_payload = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Tus-Resumable, \
            Upload-Length, Upload-Metadata, Upload-Offset, Content-Type',
            'Access-Control-Expose-Headers': 'Tus-Resumable, Upload-Length, Upload-Metadata, \
            Upload-Offset, Content-Type',
            'Access-Control-Allow-Methods': '*', 'Cache-Control': 'no-store',
            'Tus-Resumable': '1.0.0',
            'Upload-Offset': '527', 'Upload-Length': '527',
            'Content-Length': '0', 'Content-Type': 'application/octet-stream',
            'Date': 'Wed, 02 Sep 2020 12:54:17 GMT', 'Server': 'Python/3.8 aiohttp/3.6.2'}

            # file upload on storage
            m.patch(storage_path2 + "?token={}".format(storage_payload['token']), payload=tus_payload,
                    headers=tus_payload, status=204)

            m.patch(build_url(session.config, "/folders/{}/request-upload?path='{}'&size={}".format(
                             vfolder_name, mock_file, 1024)), status=200)

            resp = await session.VFolder(vfolder_name).upload([mock_file], basedir=tmp_path)

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


@pytest.mark.skip(reason="postponed test implementation")
@pytest.mark.asyncio
async def test_vfolder_download(mocker):
    mock_reader = AsyncMock()
    mock_from_response = mocker.patch(
        'ai.backend.client.func.vfolder.aiohttp.MultipartReader.from_response',
        return_value=mock_reader)
    mock_reader.next = AsyncMock()
    mock_reader.next.return_value = None
    mock_file = 'fake-file1'
    with aioresponses() as m:

        async with AsyncSession() as session:
            vfolder_name = 'fake-vfolder-name'
            # client to manager
            # manager to storage-proxy
            storage_path = str(build_url(session.config, 'folder/{}/download'
                                .format(vfolder_name))).replace('8081', '6021')
            storage_path2 = str(build_url(session.config, '/download')).replace('8081', '6021')

            payload = {'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9. \
            eyJwYXRoIjoiaHR0cDoxMjcuMC4wLjEvZm9sZGVycy9mYWtlLXZmb2xkZXItbmFtZS9yZXF1ZXN0LXVwbG9hZCIsInNpemUiOjEwMjR9.\
            5IXk0xdrr6aPzVjud4cdfcXWch7Bq-m7SlFhnUv8XL8', 'url': storage_path}

            storage_payload = {'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9. \
                eyJvcCI6InVwbG9hZCIsInZvbHVtZSI6InZvbHVtZTEiLCJ2ZmlkIjoiO \
                DBiYWYyYjgtNTY3My00MmVkLTgyZWEtYj \
                NmNzNmOWQwNjAzIiwicmVscGF0aCI6InNldHVwLmNmZyIsInNpemUiOjU \
                yNywic2Vzc2lvbiI6ImE3YzZiY2I1MWRlY2I3NzJjZjRkMDI3YjA5 \
                MGI5NGM5IiwiZXhwIjoxNTk5MTIzMzYxfQ. \
                D13UMFrz-2qq9c0k4MGpjVOMn5Z9-fyR5tRRIkvtvqk'}

            # 1. Client to Manager throught Request
            m.post(build_url(session.config, "/folders/{}/request-download?path='{}'".format(
                             vfolder_name, mock_file)), payload=payload['token'], status=200)

            # 2. Manager to storage proxy
            """
            m.post(storage_path + "?volume= \
                   volume1&vfid=80baf2b8-5673-42ed-82ea-b3f73f9d0603&relpath={}"
                   .format('fake-file1'),
                   payload=payload,
                   status=200)
            """
            # 3. Client to Manager through TusClient. Upload url

            m.get(storage_path2 + "?token={}".format(storage_payload['token']))

            m.get(build_url(session.config, "/folders/{}/request-download?path='{}'".format(
                             vfolder_name, mock_file)), status=200)

            await session.VFolder(vfolder_name).download(['fake-file1'])
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
