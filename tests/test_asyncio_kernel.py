from unittest import mock

import pytest

from ai.backend.client.compat import token_hex
from ai.backend.client.session import AsyncSession
from ai.backend.client.test_utils import AsyncContextMock, AsyncMock


@pytest.mark.asyncio
async def test_create_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=AsyncMock())
    mock_req_cls = mocker.patch('ai.backend.client.func.session.Request',
                                return_value=mock_req_obj)
    async with AsyncSession() as session:
        await session.ComputeSession.get_or_create('python:3.6-ubuntu18.04')
        mock_req_cls.assert_called_once_with(
            session, 'POST', '/session/create')
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_create_kernel_return_id_only(mocker):
    return_value = {'sessionId': 'mock_sess_id'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201, json=mock_json_coro)
    mocker.patch('ai.backend.client.func.session.Request',
                 return_value=mock_req_obj)
    async with AsyncSession() as session:
        cs = await session.ComputeSession.get_or_create('python:3.6-ubuntu18.04')
        assert cs.session_id == return_value['sessionId']


@pytest.mark.asyncio
async def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    session_id = token_hex(12)
    mock_req_cls = mocker.patch('ai.backend.client.func.session.Request',
                                return_value=mock_req_obj)
    async with AsyncSession() as session:
        await session.ComputeSession(session_id).destroy()
        mock_req_cls.assert_called_once_with(
            session, 'DELETE', '/session/{}'.format(session_id), params={})


@pytest.mark.asyncio
async def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    session_id = token_hex(12)
    mock_req_cls = mocker.patch('ai.backend.client.func.session.Request',
                                return_value=mock_req_obj)
    async with AsyncSession() as session:
        await session.ComputeSession(session_id).restart()
        mock_req_cls.assert_called_once_with(
            session, 'PATCH', '/session/{}'.format(session_id), params={})


@pytest.mark.asyncio
async def test_get_kernel_info_url(mocker):
    return_value = {}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=200, json=mock_json_coro)
    session_id = token_hex(12)
    mock_req_cls = mocker.patch('ai.backend.client.func.session.Request',
                                return_value=mock_req_obj)
    async with AsyncSession() as session:
        await session.ComputeSession(session_id).get_info()
        mock_req_cls.assert_called_once_with(
            session, 'GET', '/session/{}'.format(session_id), params={})


@pytest.mark.asyncio
async def test_execute_code_url(mocker):
    return_value = {'result': 'hi'}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=200, json=mock_json_coro)
    session_id = token_hex(12)
    run_id = token_hex(8)
    mock_req_cls = mocker.patch('ai.backend.client.func.session.Request',
                                return_value=mock_req_obj)
    async with AsyncSession() as session:
        await session.ComputeSession(session_id).execute(run_id, 'hello')
        mock_req_cls.assert_called_once_with(
            session, 'POST', '/session/{}'.format(session_id),
            params={})
