from pathlib import Path
from unittest import mock

import secrets
import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import AsyncSession
from ai.backend.client.request import Request, Response
from ai.backend.client.test_utils import AsyncMock

from aiotusclient import client


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


@pytest.mark.asyncio
async def test_tus_upload(tmp_path: Path):

    basedir = tmp_path / 'example.bin'
    mock_file = basedir
    mock_file.write_bytes(secrets.token_bytes(1024))
    vfolder_name = 'fake-vfolder-name'
    with aioresponses() as m:

        tus_client = client.TusClient()
        input_file = open(basedir, "rb")
        print(f"Uploading {basedir} ...")
        # TODO: refactor out the progress bar
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9pwd.\
            eyJwYXRoIjoiaHR0cDoxMjcuMC4wLjEvZm9sZGVycy9mYWtlLXZmb2xkZXItbmFtZS9yZXF1ZXN0LXVwbG9hZCIsInNpemUiOjEwMjR9.\
                5IXk0xdrr6aPzVjud4cdfcXWch7Bq-m7SlFhnUv8XL8"

        storage_proxy_payload = {'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers':
        'Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type',
        'Access-Control-Expose-Headers':
        'Tus-Resumable, Upload-Length, Upload-Metadata, Upload-Offset, Content-Type',
        'Access-Control-Allow-Methods': '*',
        'Cache-Control': 'no-store',
        'Tus-Resumable': '1.0.0',
        'Upload-Offset': '1024',
        'Upload-Length': '1024',
        'Content-Length': '0',
        'Content-Type': 'application/octet-stream',
        'Date': 'Thu, 10 Sep 2020 05:52:12 GMT',
        'Server': 'Python/3.8 aiohttp/3.6.2'}

        upload_url = 'http://127.0.0.1:6021/upload?token={}'.format(token)
        m.head('http://127.0.0.1:6021/folders/{}/upload?token={}'.format(vfolder_name, token),
               status=200)
        m.patch('http://127.0.0.1:6021/upload?token={}'.format(token),
                payload=storage_proxy_payload, status=204,
                headers={'upload-offset': '1024',
                         'Content-Type': 'application/offset+octet-stream',
                         'Tus-Resumable': '1.0.0'})

        uploader = tus_client.async_uploader(
            file_stream=input_file,
            url=upload_url,
            upload_checksum=False,
            chunk_size=1024,
            retries=1, retry_delay=1)

        res = await uploader.upload()
        if res is None:
            assert True
        else:
            assert False


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
