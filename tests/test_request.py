import asyncio
from collections import OrderedDict
import io
import json

import aiohttp
from aioresponses import aioresponses
import pytest

from ai.backend.client.exceptions import BackendClientError
from ai.backend.client.request import Request, Response, StreamingResponse
from ai.backend.client.session import Session, AsyncSession


@pytest.fixture
def mock_request_params(defconfig):
    with Session(config=defconfig) as session:
        yield OrderedDict(
            session=session,
            method='GET',
            path='/function/item/',
            content=OrderedDict(test1='1'),
        )


def test_request_initialization(mock_request_params):
    rqst = Request(**mock_request_params)

    assert rqst.session == mock_request_params['session']
    assert rqst.method == mock_request_params['method']
    assert rqst.path == mock_request_params['path'].lstrip('/')
    assert rqst.content == mock_request_params['content']
    assert 'X-BackendAI-Version' in rqst.headers
    assert rqst._content == json.dumps(mock_request_params['content']).encode('utf8')


def test_content_is_auto_set_to_blank_if_no_data(mock_request_params):
    mock_request_params = mock_request_params.copy()
    mock_request_params['content'] = None
    rqst = Request(**mock_request_params)

    assert rqst.content_type == 'application/octet-stream'
    assert rqst.content == b''


def test_content_is_blank(mock_request_params):
    mock_request_params['content'] = OrderedDict()
    rqst = Request(**mock_request_params)

    assert rqst.content_type == 'application/json'
    assert rqst.content == {}


def test_content_is_bytes(mock_request_params):
    mock_request_params['content'] = b'\xff\xf1'
    rqst = Request(**mock_request_params)

    assert rqst.content_type == 'application/octet-stream'
    assert rqst.content == b'\xff\xf1'


def test_content_is_text(mock_request_params):
    mock_request_params['content'] = 'hello'
    rqst = Request(**mock_request_params)

    assert rqst.content_type == 'text/plain'
    assert rqst.content == 'hello'


def test_content_is_files(mock_request_params):
    files = [
        ('src', 'test1.txt', io.BytesIO(), 'application/octet-stream'),
        ('src', 'test2.txt', io.BytesIO(), 'application/octet-stream'),
    ]
    mock_request_params['content'] = files
    rqst = Request(**mock_request_params)

    assert rqst.content_type == 'multipart/form-data'
    assert rqst.content == files


def test_set_content_correctly(mock_request_params):
    mock_request_params['content'] = OrderedDict()
    rqst = Request(**mock_request_params)
    new_data = b'new-data'

    assert not rqst.content
    rqst.content = new_data
    assert rqst.content == new_data
    assert rqst.headers['Content-Length'] == str(len(new_data))


def test_build_correct_url(mock_request_params):
    rqst = Request(**mock_request_params)
    path = '/' + rqst.path if len(rqst.path) > 0 else ''
    canonical_url = 'http://127.0.0.1:8081{0}'.format(path)
    assert rqst.build_url() == canonical_url


def test_fetch_not_allowed_request_raises_error(mock_request_params):
    mock_request_params['method'] = 'STRANGE'
    rqst = Request(**mock_request_params)

    with pytest.raises(AssertionError):
        rqst.fetch()


def test_fetch(dummy_endpoint):
    # Request.fetch() now calls Request.afetch() internally.
    with aioresponses() as m, Session() as session:
        body = b'hello world'
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'text/plain; charset=utf-8',
                     'Content-Length': str(len(body))},
        )
        rqst = Request(session, 'POST', 'function')
        resp = rqst.fetch()
        assert isinstance(resp, Response)
        assert resp.status == 200
        assert resp.charset == 'utf-8'
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
        resp = rqst.fetch()
        assert isinstance(resp, Response)
        assert resp.status == 200
        assert resp.charset == 'utf-8'
        assert resp.content_type == 'application/json'
        assert resp.text() == body.decode()
        assert resp.json() == {'a': 1234, 'b': None}
        assert resp.content_length == len(body)


# TODO: fix up
@pytest.mark.xfail
def test_streaming_fetch(dummy_endpoint):
    # Read content by chunks.
    with aioresponses() as m, Session() as session:
        body = b'hello world'
        m.post(
            dummy_endpoint + 'function', status=200, body=body,
            headers={'Content-Type': 'text/plain; charset=utf-8',
                     'Content-Length': str(len(body))},
        )
        rqst = Request(session, 'POST', 'function', streaming=True)
        resp = rqst.fetch()
        assert isinstance(resp, StreamingResponse)
        assert resp.status == 200
        assert resp.content_type == 'text/plain'
        assert not resp.stream.at_eof
        assert resp.read(3) == b'hel'
        assert resp.read(2) == b'lo'
        assert not resp.stream.at_eof
        resp.read()
        assert resp.stream.at_eof
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
        resp = rqst.fetch()
        assert isinstance(resp, Response)
        assert resp.status == 404
        assert resp.charset == 'utf-8'
        assert resp.content_type == 'application/problem+json'
        assert resp.text() == body.decode()
        assert resp.content_length == len(body)
        data = resp.json()
        assert data['type'] == 'https://api.backend.ai/probs/kernel-not-found'
        assert data['title'] == 'Kernel Not Found'


@pytest.mark.asyncio
async def test_afetch_not_allowed_request_raises_error():
    async with AsyncSession() as session:
        rqst = Request(session, 'STRANGE', '/')
        with pytest.raises(AssertionError):
            await rqst.afetch()


@pytest.mark.asyncio
async def test_afetch_client_error(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession() as session:
            m.post(dummy_endpoint,
                   exception=aiohttp.ClientConnectionError())
            rqst = Request(session, 'POST', '/')
            with pytest.raises(BackendClientError):
                await rqst.afetch()


@pytest.mark.asyncio
async def test_afetch_cancellation(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession() as session:
            m.post(dummy_endpoint,
                   exception=asyncio.CancelledError())
            rqst = Request(session, 'POST', '/')
            with pytest.raises(asyncio.CancelledError):
                await rqst.afetch()


@pytest.mark.asyncio
async def test_afetch_timeout(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession() as session:
            m.post(dummy_endpoint,
                   exception=asyncio.TimeoutError())
            rqst = Request(session, 'POST', '/')
            with pytest.raises(asyncio.TimeoutError):
                await rqst.afetch()


def test_response_initialization():
    body = b'my precious content \xea\xb0\x80..'
    mock_session = object()
    mock_resp = object()
    resp = Response(mock_session, mock_resp,
                    body=body,
                    content_type='text/plain')
    assert resp.session is mock_session
    assert resp.raw_response is mock_resp
    assert resp.content_type == 'text/plain'
    assert resp.text() == 'my precious content 가..'
    assert resp.content_length == len(body)
