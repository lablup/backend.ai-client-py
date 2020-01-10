from unittest import mock

from ai.backend.client.compat import token_hex
from ai.backend.client.config import APIConfig
from ai.backend.client.session import Session
from ai.backend.client.test_utils import AsyncContextMock, AsyncMock


def test_create_with_config(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=AsyncMock())
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)

    myconfig = APIConfig(
        endpoint='https://localhost:9999',
        access_key='1234',
        secret_key='asdf',
        user_agent='BAIClientTest'
    )
    with Session(config=myconfig) as session:
        assert session.config is myconfig
        cs = session.ComputeSession.get_or_create('python')
        mock_req.assert_called_once_with(session, 'POST', '/session/create')
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
        session.ComputeSession.get_or_create('python:3.6-ubuntu18.04')
        mock_req.assert_called_once_with(session, 'POST', '/session/create')
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_create_kernel_return_id_only(mocker):
    return_value = {'sessionId': 'mock_session_id'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=mock_json_coro)
    mocker.patch('ai.backend.client.func.session.Request', return_value=mock_req_obj)

    with Session() as session:
        cs = session.ComputeSession.get_or_create('python:3.6-ubuntu18.04')
        assert cs.session_id == return_value['sessionId']


def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        cs.destroy()

    mock_req.assert_called_once_with(session,
                                     'DELETE', '/session/{}'.format(session_id),
                                     params={})
    mock_req_obj.fetch.assert_called_once_with()


def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mock_req = mocker.patch('ai.backend.client.func.session.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        cs.restart()

        mock_req.assert_called_once_with(session,
                                         'PATCH', '/session/{}'.format(session_id),
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
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        cs.get_info()

        mock_req.assert_called_once_with(session,
                                         'GET', '/session/{}'.format(session_id),
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
        session_id = token_hex(12)
        cs = session.ComputeSession(session_id)
        run_id = token_hex(8)
        cs.execute(run_id, 'hello')

        mock_req.assert_called_once_with(
            session, 'POST', '/session/{}'.format(session_id),
            params={}
        )
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()
