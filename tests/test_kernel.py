from unittest import mock

from ai.backend.client.compat import token_hex
from ai.backend.client.config import APIConfig
from ai.backend.client.session import Session
from ai.backend.client.test_utils import AsyncContextMock, AsyncMock


def test_create_with_config(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=AsyncMock())
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    myconfig = APIConfig(
        endpoint='https://localhost:9999',
        access_key='1234',
        secret_key='asdf',
        user_agent='BAIClientTest'
    )
    with Session(config=myconfig) as session:
        assert session.config is myconfig
        k = session.Kernel.get_or_create('python')
        mock_req.assert_called_once_with(session, 'POST', '/kernel/create')
        assert str(k.session.config.endpoint) == 'https://localhost:9999'
        assert k.session.config.user_agent == 'BAIClientTest'
        assert k.session.config.access_key == '1234'
        assert k.session.config.secret_key == 'asdf'


def test_create_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=AsyncMock())
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        session.Kernel.get_or_create('python:3.6-ubuntu18.04')
        mock_req.assert_called_once_with(session, 'POST', '/kernel/create')
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_create_kernel_return_id_only(mocker):
    return_value = {'kernelId': 'mock_kernel_id'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=mock_json_coro)
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    with Session() as session:
        k = session.Kernel.get_or_create('python:3.6-ubuntu18.04')
        assert k.kernel_id == return_value['kernelId']


def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        k.destroy()

    mock_req.assert_called_once_with(session,
                                     'DELETE', '/kernel/{}'.format(kernel_id),
                                     params={})
    mock_req_obj.fetch.assert_called_once_with()


def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        k.restart()

        mock_req.assert_called_once_with(session,
                                         'PATCH', '/kernel/{}'.format(kernel_id),
                                         params={})
        mock_req_obj.fetch.assert_called_once_with()


def test_get_kernel_info_url(mocker):
    return_value = {}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=200, json=mock_json_coro)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        k.get_info()

        mock_req.assert_called_once_with(session,
                                         'GET', '/kernel/{}'.format(kernel_id),
                                         params={})
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_execute_code_url(mocker):
    return_value = {'result': 'hi'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=200, json=mock_json_coro)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        run_id = token_hex(8)
        k.execute(run_id, 'hello')

        mock_req.assert_called_once_with(
            session, 'POST', '/kernel/{}'.format(kernel_id),
            params={}
        )
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()
