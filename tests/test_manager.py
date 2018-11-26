from unittest import mock

from ai.backend.client.session import Session


def test_status(mocker):
    mock_json_func = lambda: {'status': 'running', 'active_sessions': 3}
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(
        status=200, json=mock_json_func
    )
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        resp = session.Manager.status()

        mock_req_obj.fetch.assert_called_once_with()
        assert resp['status'] == mock_json_func()['status']
        assert resp['active_sessions'] == mock_json_func()['active_sessions']


def test_freeze(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=204)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze()

        mock_req_obj.fetch.assert_called_once_with()


def test_freeze_opt_force_kill(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=204)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze(force_kill=True)

        mock_req_obj.fetch.assert_called_once_with()


def test_unfreeze(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = mock.MagicMock(status=204)
    mocker.patch('ai.backend.client.manager.Request', return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze()

        mock_req_obj.fetch.assert_called_once_with()
