from unittest import mock

import pytest

from ai.backend.client.compat import token_hex
from ai.backend.client.config import APIConfig
from ai.backend.client.session import Session
from ai.backend.client.func.session import get_session_api_prefix
from ai.backend.client.test_utils import AsyncContextMock, AsyncMock


simulated_api_versions = [
    (4, '20190615'),
    (5, '20191215'),
]


@pytest.fixture(scope='module', autouse=True, params=simulated_api_versions)
def api_version(request):
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = request.param
    with mock.patch('ai.backend.client.session._negotiate_api_version', mock_nego_func):
        yield request.param


def test_create_with_config(mocker, api_version):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=AsyncMock())
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)
    myconfig = APIConfig(
        endpoint='https://localhost:9999',
        access_key='1234',
        secret_key='asdf',
        user_agent='BAIClientTest',
        version=f'v{api_version[0]}.{api_version[1]}',
    )
    with Session(config=myconfig) as session:
        prefix = get_session_api_prefix(session.api_version)
        if api_version[0] == 4:
            assert prefix == 'kernel'
        else:
            assert prefix == 'session'
        assert session.config is myconfig
        cs = session.ComputeSession.get_or_create('python')
        mock_req.assert_called_once_with(session, 'POST', f'/{prefix}/create')
        assert str(cs.session.config.endpoint) == 'https://localhost:9999'
        assert cs.session.config.user_agent == 'BAIClientTest'
        assert cs.session.config.access_key == '1234'
        assert cs.session.config.secret_key == 'asdf'


def test_create_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=AsyncMock())
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)
    with Session() as session:
        prefix = get_session_api_prefix(session.api_version)
        session.ComputeSession.get_or_create('python:3.6-ubuntu18.04')
        mock_req.assert_called_once_with(session, 'POST', f'/{prefix}/create')
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_create_kernel_return_id_only(mocker, api_version):
    if api_version[0] == 4:
        return_value = {'kernelId': 'mock_sess_id'}
    else:
        return_value = {'sessionId': 'mock_sess_id'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=mock_json_coro)
    mocker.patch('ai.backend.client.func.session.Request', return_value=mock_req_obj)
    with Session() as session:
        prefix = get_session_api_prefix(session.api_version)
        cs = session.ComputeSession.get_or_create('python:3.6-ubuntu18.04')
        assert cs.session_id == return_value[f'{prefix}Id']


def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)
    with Session() as session:
        prefix = get_session_api_prefix(session.api_version)
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        cs.destroy()
        mock_req.assert_called_once_with(
            session,
            'DELETE', f'/{prefix}/{session_id}',
            params={})
        mock_req_obj.fetch.assert_called_once_with()


def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)
    with Session() as session:
        prefix = get_session_api_prefix(session.api_version)
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        cs.restart()
        mock_req.assert_called_once_with(
            session,
            'PATCH', f'/{prefix}/{session_id}',
            params={})
        mock_req_obj.fetch.assert_called_once_with()


def test_get_kernel_info_url(mocker):
    return_value = {}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=200, json=mock_json_coro)
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)
    with Session() as session:
        prefix = get_session_api_prefix(session.api_version)
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        cs.get_info()
        mock_req.assert_called_once_with(
            session,
            'GET', f'/{prefix}/{session_id}',
            params={})
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_execute_code_url(mocker):
    return_value = {'result': 'hi'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=200, json=mock_json_coro)
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)
    with Session() as session:
        prefix = get_session_api_prefix(session.api_version)
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        run_id = token_hex(8)
        cs.execute(run_id, 'hello')
        mock_req.assert_called_once_with(
            session, 'POST', f'/{prefix}/{session_id}',
            params={}
        )
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()
