import asyncio
import io
import json

import aiohttp
from aioresponses import aioresponses
import pytest

from ai.backend.client.exceptions import BackendClientError, BackendAPIError
from ai.backend.client.request import Request, Response, AttachedFile
from ai.backend.client.session import Session, AsyncSession


@pytest.fixture
def session(defconfig):
    with Session(config=defconfig) as session:
        yield session


@pytest.fixture
def mock_request_params(session):
    yield {
        'session': session,
        'method': 'GET',
        'path': '/function/item/',
        'content': b'{"test1": 1}',
        'content_type': 'application/json',
    }


def test_request_initialization(mock_request_params):
    rqst = Request(**mock_request_params)

    assert rqst.session == mock_request_params['session']
    assert rqst.method == mock_request_params['method']
    assert rqst.path == mock_request_params['path'].lstrip('/')
    assert rqst.content == mock_request_params['content']
    assert 'X-BackendAI-Version' in rqst.headers


def test_request_set_content_none(mock_request_params):
    mock_request_params = mock_request_params.copy()
    mock_request_params['content'] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b''
    assert rqst._pack_content() is rqst.content


def test_request_set_content(mock_request_params):
    rqst = Request(**mock_request_params)
    assert rqst.content == mock_request_params['content']
    assert rqst.content_type == 'application/json'
    assert rqst._pack_content() is rqst.content

    mock_request_params['content'] = 'hello'
    mock_request_params['content_type'] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b'hello'
    assert rqst.content_type == 'text/plain'
    assert rqst._pack_content() is rqst.content

    mock_request_params['content'] = b'\x00\x01\xfe\xff'
    mock_request_params['content_type'] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b'\x00\x01\xfe\xff'
    assert rqst.content_type == 'application/octet-stream'
    assert rqst._pack_content() is rqst.content


def test_request_attach_files(mock_request_params):
    files = [
        AttachedFile('test1.txt', io.BytesIO(), 'application/octet-stream'),
        AttachedFile('test2.txt', io.BytesIO(), 'application/octet-stream'),
    ]

    mock_request_params['content'] = b'something'
    rqst = Request(**mock_request_params)
    with pytest.raises(AssertionError):
        rqst.attach_files(files)

    mock_request_params['content'] = b''
    rqst = Request(**mock_request_params)
    rqst.attach_files(files)

    assert rqst.content_type == 'multipart/form-data'
    assert rqst.content == b''
    packed_content = rqst._pack_content()
    assert packed_content.is_multipart


def test_build_correct_url(mock_request_params):
    canonical_url = 'http://127.0.0.1:8081/function'

    mock_request_params['path'] = '/function'
    rqst = Request(**mock_request_params)
    assert rqst._build_url() == canonical_url

    mock_request_params['path'] = 'function'
    rqst = Request(**mock_request_params)
    assert rqst._build_url() == canonical_url


def test_fetch_invalid_method(mock_request_params):
    mock_request_params['method'] = 'STRANGE'
    rqst = Request(**mock_request_params)

    with pytest.raises(AssertionError):
        with rqst.fetch():
            pass


def test_fetch(dummy_endpoint):
    with aioresponses() as m, Session() as session:
        body = b'hello world'
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'text/plain; charset=utf-8',
                     'Content-Length': str(len(body))},
        )
        rqst = Request(session, 'POST', 'function')
        with rqst.fetch() as resp:
            assert isinstance(resp, Response)
            assert resp.status == 200
            assert resp.content_type == 'text/plain'
            assert resp.text() == body.decode()
            assert resp.content_length == len(body)

    with aioresponses() as m, Session() as session:
        body = b'{"a": 1234, "b": null}'
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'application/json; charset=utf-8',
                     'Content-Length': str(len(body))},
        )
        rqst = Request(session, 'POST', 'function')
        with rqst.fetch() as resp:
            assert isinstance(resp, Response)
            assert resp.status == 200
            assert resp.content_type == 'application/json'
            assert resp.text() == body.decode()
            assert resp.json() == {'a': 1234, 'b': None}
            assert resp.content_length == len(body)


def test_streaming_fetch(dummy_endpoint):
    # Read content by chunks.
    with aioresponses() as m, Session() as session:
        body = b'hello world'
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'text/plain; charset=utf-8',
                     'Content-Length': str(len(body))},
        )
        rqst = Request(session, 'POST', 'function')
        with rqst.fetch() as resp:
            assert resp.status == 200
            assert resp.content_type == 'text/plain'
            assert resp.read(3) == b'hel'
            assert resp.read(2) == b'lo'
            resp.read()
            with pytest.raises(AssertionError):
                assert resp.text()


def test_invalid_requests(dummy_endpoint):
    with aioresponses() as m, Session() as session:
        body = json.dumps({
            'type': 'https://api.backend.ai/probs/kernel-not-found',
            'title': 'Kernel Not Found',
        }).encode('utf8')
        m.post(
            dummy_endpoint, status=404, body=body,
            headers={'Content-Type': 'application/problem+json; charset=utf-8',
                     'Content-Length': str(len(body))},
        )
        rqst = Request(session, 'POST', '/')
        with pytest.raises(BackendAPIError) as e:
            with rqst.fetch():
                pass
            assert e.status == 404
            assert e.data['type'] == 'https://api.backend.ai/probs/kernel-not-found'
            assert e.data['title'] == 'Kernel Not Found'


@pytest.mark.asyncio
async def test_fetch_invalid_method_async():
    async with AsyncSession() as session:
        rqst = Request(session, 'STRANGE', '/')
        with pytest.raises(AssertionError):
            async with rqst.fetch():
                pass


@pytest.mark.asyncio
async def test_fetch_client_error_async(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession() as session:
            m.post(dummy_endpoint,
                   exception=aiohttp.ClientConnectionError())
            rqst = Request(session, 'POST', '/')
            with pytest.raises(BackendClientError):
                async with rqst.fetch():
                    pass


@pytest.mark.asyncio
async def test_fetch_cancellation_async(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession() as session:
            m.post(dummy_endpoint,
                   exception=asyncio.CancelledError())
            rqst = Request(session, 'POST', '/')
            with pytest.raises(asyncio.CancelledError):
                async with rqst.fetch():
                    pass


@pytest.mark.asyncio
async def test_fetch_timeout_async(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession() as session:
            m.post(dummy_endpoint,
                   exception=asyncio.TimeoutError())
            rqst = Request(session, 'POST', '/')
            with pytest.raises(asyncio.TimeoutError):
                async with rqst.fetch():
                    pass


def test_response_sync(defconfig, dummy_endpoint):
    body = b'{"test": 1234}'
    with aioresponses() as m:
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'application/json',
                     'Content-Length': str(len(body))},
        )
        with Session(config=defconfig) as session:
            rqst = Request(session, 'POST', '/function')
            with rqst.fetch() as resp:
                assert resp.text() == '{"test": 1234}'
                assert resp.json() == {'test': 1234}


@pytest.mark.asyncio
async def test_response_async(defconfig, dummy_endpoint):
    body = b'{"test": 5678}'
    with aioresponses() as m:
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'application/json',
                     'Content-Length': str(len(body))},
        )
        async with AsyncSession(config=defconfig) as session:
            rqst = Request(session, 'POST', '/function')
            async with rqst.fetch() as resp:
                assert await resp.text() == '{"test": 5678}'
                assert await resp.json() == {'test': 5678}
