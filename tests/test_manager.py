from unittest import mock

from ai.backend.client.session import Session
from ai.backend.client.test_utils import AsyncMock, AsyncContextMock


def test_status(mocker):
    return_value = {'status': 'running', 'active_sessions': 3}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mocker.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=200,
                                                       json=mock_json_coro)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        resp = session.Manager.status()
        mock_req_obj.fetch.assert_called_once_with()
        assert resp['status'] == return_value['status']
        assert resp['active_sessions'] == return_value['active_sessions']


def test_freeze(mocker):
    mock_req_obj = mocker.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze()
        mock_req_obj.fetch.assert_called_once_with()


def test_freeze_opt_force_kill(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze(force_kill=True)
        mock_req_obj.fetch.assert_called_once_with()


def test_unfreeze(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        session.Manager.unfreeze()
        mock_req_obj.fetch.assert_called_once_with()
