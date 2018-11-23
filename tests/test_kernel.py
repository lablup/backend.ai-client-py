from unittest import mock

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.compat import token_hex
from ai.backend.client.config import APIConfig
from ai.backend.client.kernel import Kernel
from ai.backend.client.session import Session


def test_create_with_config(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mocker.MagicMock(status=201,
                                                       json=mock.MagicMock())
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
        mock_req.assert_called_once_with(session,
                                         'POST', '/kernel/create', mocker.ANY)
        assert str(k.session.config.endpoint) == 'https://localhost:9999'
        assert k.session.config.user_agent == 'BAIClientTest'
        assert k.session.config.access_key == '1234'
        assert k.session.config.secret_key == 'asdf'


def test_deprecated_api():
    with pytest.raises(AssertionError):
        Kernel.get_or_create('python')


def test_create_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mocker.MagicMock(status=201,
                                                       json=mock.MagicMock())
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        session.Kernel.get_or_create('python')
        mock_req.assert_called_once_with(session, 'POST', '/kernel/create',
                                         mocker.ANY)
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_create_kernel_return_id_only(mocker):
    mock_json_func = lambda: {'kernelId': 'mock_kernel_id'}
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(
        status=201, json=mock_json_func
    )
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    with Session() as session:
        k = session.Kernel.get_or_create('python')
        assert k.kernel_id == mock_json_func()['kernelId']


def test_create_kernel_raises_err_with_abnormal_status(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=400)
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    with Session() as session:
        with pytest.raises(BackendAPIError):
            session.Kernel.get_or_create('python')


def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=204)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        k.destroy()

    mock_req.assert_called_once_with(session,
                                     'DELETE', '/kernel/{}'.format(kernel_id))
    mock_req_obj.fetch.assert_called_once_with()


def test_destroy_kernel_raises_err_with_abnormal_status(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=400)
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    kernel_id = token_hex(12)
    with Session() as session:
        with pytest.raises(BackendAPIError):
            k = session.Kernel(kernel_id)
            k.destroy()


def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=204)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        k.restart()

        mock_req.assert_called_once_with(session,
                                         'PATCH', '/kernel/{}'.format(kernel_id))
        mock_req_obj.fetch.assert_called_once_with()


def test_restart_kernel_raises_err_with_abnormal_status(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=400)
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    kernel_id = token_hex(12)
    with Session() as session:
        with pytest.raises(BackendAPIError):
            k = session.Kernel(kernel_id)
            k.restart()


def test_get_kernel_info_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=200)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        k.get_info()

        mock_req.assert_called_once_with(session,
                                         'GET', '/kernel/{}'.format(kernel_id))
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_get_kernel_info_raises_err_with_abnormal_status(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=400)
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    kernel_id = token_hex(12)
    with Session() as session:
        with pytest.raises(BackendAPIError):
            k = session.Kernel(kernel_id)
            k.get_info()


def test_execute_code_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=200)
    mock_req = mocker.patch('ai.backend.client.kernel.Request',
                            return_value=mock_req_obj)

    with Session() as session:
        kernel_id = token_hex(12)
        k = session.Kernel(kernel_id)
        run_id = token_hex(8)
        k.execute(run_id, 'hello')

        mock_req.assert_called_once_with(
            session, 'POST', '/kernel/{}'.format(kernel_id),
            {'mode': 'query', 'runId': run_id, 'code': 'hello'})
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_execute_code_raises_err_with_abnormal_status(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=400)
    mocker.patch('ai.backend.client.kernel.Request', return_value=mock_req_obj)

    kernel_id = token_hex(12)
    run_id = token_hex(8)
    with Session() as session:
        with pytest.raises(BackendAPIError):
            k = session.Kernel(kernel_id)
            k.execute(run_id, 'hello')
