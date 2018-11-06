from unittest import mock

import aiohttp
import asynctest
import pytest

from ai.backend.client.compat import token_hex
from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.kernel import StreamPty
from ai.backend.client.request import Request, Response
from ai.backend.client.session import AsyncSession


@pytest.mark.asyncio
async def test_create_kernel_url(mocker):
    mock_resp = asynctest.MagicMock(spec=Response)
    mock_resp.status = 201
    mock_resp.json = asynctest.MagicMock()

    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = mock_resp

    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj) as mock_req_cls:
            await session.Kernel.get_or_create('python')

            mock_req_cls.assert_called_once_with(
                session, 'POST', '/kernel/create', mock.ANY)
            mock_req_obj.afetch.assert_called_once_with()
            mock_req_obj.afetch.return_value.json.assert_called_once_with()


@pytest.mark.asyncio
async def test_create_kernel_return_id_only():
    mock_resp = asynctest.MagicMock(spec=Response)
    mock_resp.status = 201
    mock_resp.json = lambda: {'kernelId': 'mock_kernel_id'}

    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = mock_resp

    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            k = await session.Kernel.get_or_create('python')

            assert k.kernel_id == mock_resp.json()['kernelId']


@pytest.mark.asyncio
async def test_create_kernel_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=400)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            with pytest.raises(BackendAPIError):
                await session.Kernel.get_or_create('python')


@pytest.mark.asyncio
async def test_destroy_kernel_url(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=204)
    kernel_id = token_hex(12)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj) as mock_req_cls:
            await session.Kernel(kernel_id).destroy()
            mock_req_cls.assert_called_once_with(
                session, 'DELETE', '/kernel/{}'.format(kernel_id))


@pytest.mark.asyncio
async def test_destroy_kernel_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=400)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            with pytest.raises(BackendAPIError):
                await session.Kernel('mykernel').destroy()


@pytest.mark.asyncio
async def test_restart_kernel_url(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=204)
    kernel_id = token_hex(12)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj) as mock_req_cls:
            await session.Kernel(kernel_id).restart()
            mock_req_cls.assert_called_once_with(
                session, 'PATCH', '/kernel/{}'.format(kernel_id))


@pytest.mark.asyncio
async def test_restart_kernel_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=400)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            with pytest.raises(BackendAPIError):
                await session.Kernel('mykernel').restart()


@pytest.mark.asyncio
async def test_get_kernel_info_url(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=200)
    kernel_id = token_hex(12)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj) as mock_req_cls:
            await session.Kernel(kernel_id).get_info()
            mock_req_cls.assert_called_once_with(
                session, 'GET', '/kernel/{}'.format(kernel_id))


@pytest.mark.asyncio
async def test_get_kernel_info_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=400)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            with pytest.raises(BackendAPIError):
                await session.Kernel('mykernel').get_info()


@pytest.mark.asyncio
async def test_execute_code_url(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=200)
    kernel_id = token_hex(12)
    run_id = token_hex(8)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj) as mock_req_cls:
            await session.Kernel(kernel_id).execute(run_id, 'hello')
            mock_req_cls.assert_called_once_with(
                session, 'POST', '/kernel/{}'.format(kernel_id),
                {'mode': 'query', 'runId': run_id, 'code': 'hello'})


@pytest.mark.asyncio
async def test_execute_code_raises_err_with_abnormal_status():
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_req_obj.afetch.return_value = asynctest.MagicMock(status=400)
    run_id = token_hex(8)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            with pytest.raises(BackendAPIError):
                await session.Kernel('mykernel').execute(run_id, 'hello')


@pytest.mark.asyncio
async def test_stream_pty(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    ws = object()
    mock_req_obj.connect_websocket.return_value = None, ws
    kernel_id = token_hex(12)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj) as mock_req_cls:
            stream = await session.Kernel(kernel_id).stream_pty()
            mock_req_cls.assert_called_once_with(
                session, 'GET', '/stream/kernel/{}/pty'.format(kernel_id))
            mock_req_obj.connect_websocket.assert_called_once_with()
            assert isinstance(stream, StreamPty)
            assert stream.ws is ws


@pytest.mark.asyncio
async def test_stream_pty_raises_error_with_abnormal_status(mocker):
    mock_req_obj = asynctest.MagicMock(spec=Request)
    mock_exception = aiohttp.ClientResponseError(
        None, None, code=400,
        message='emulated-handshake-error')
    mock_req_obj.connect_websocket = \
        asynctest.MagicMock(side_effect=mock_exception)
    async with AsyncSession() as session:
        with asynctest.patch('ai.backend.client.kernel.Request',
                             return_value=mock_req_obj):
            with pytest.raises(BackendClientError):
                await session.Kernel('mykernel').stream_pty()
