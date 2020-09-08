from pathlib import Path
from unittest import mock

import secrets
import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import Session, AsyncSession
from ai.backend.client.test_utils import AsyncMock
from ai.backend.client.request import Request, Response

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
        async with AsyncSession() as session:


            tus_client = client.TusClient()
            
            input_file = open(basedir, "rb")
            
            print(f"Uploading {basedir} ...")
            # TODO: refactor out the progress bar
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9pwd. \
            eyJwYXRoIjoiaHR0cDoxMjcuMC4wLjEvZm9sZGVycy9mYWtlLXZmb2xkZXItbmFtZS9yZXF1ZXN0LXVwbG9hZCIsInNpemUiOjEwMjR9.\
            5IXk0xdrr6aPzVjud4cdfcXWch7Bq-m7SlFhnUv8XL8"
            payload = {"token":token}

            upload_url = build_url(session.config, '/folders/{}/upload?token='.format(vfolder_name, token))

            m.post(build_url(session.config, '/folders/{}/upload?token='.format(vfolder_name, token)), status=200)

            uploader = tus_client.async_uploader(
                file_stream=input_file,
                url=upload_url,
                upload_checksum=False,
                chunk_size=1024,
            )
            res = await uploader.upload()
            print(res)
            assert 0 #res == ""