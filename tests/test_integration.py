'''
Integration Test Suite for Backend Client API Library.

You should be running the API service on http://localhost:8081 to run this test
suite.  Of course, the service must be fully configured as follows:

 - The gateway server must have at least one agent.

   An example sequence to run both manager & agent locally:

   docker run -e POSTGRES_DB=sorna \
              -e POSTGRES_PASSWORD=develove \
              -p 5432:5432 -d \
              --name sorna-db \
              postgres
   python -m ai.backend.client.gateway.models \
          --create-tables --populate-fixtures
   docker run -p 6379:6379 -d \
              --name sorna-redis \
              redis
   python -m ai.backend.client.agent.server \
          --volume-root=`pwd`/volume-temp --max-kernels 3
   python -m ai.backend.client.gateway.server --service-port=8081

 - The agent should have access to a Docker daemon and the
   "lablup/kernel-python:latest" docker image.

 - The gateway must have access to a test database that has pre-populated
   fixture data.
   (Check out `python -m ai.backend.client.gateway.models --populate-fixtures`)
'''

import textwrap
import time
import uuid

import pytest

from ai.backend.client.compat import token_hex
from ai.backend.client.request import Request
from ai.backend.client.config import APIConfig
from ai.backend.client import Session, AsyncSession
from ai.backend.client.exceptions import BackendAPIError


def aggregate_console(c):
    return {
        'stdout': ''.join(item[1] for item in c if item[0] == 'stdout'),
        'stderr': ''.join(item[1] for item in c if item[0] == 'stderr'),
        'html': ''.join(item[1] for item in c if item[0] == 'html'),
        'media': list(item[1] for item in c if item[0] == 'media'),
    }


@pytest.fixture
def intgr_config():
    return APIConfig(
        endpoint='http://localhost:8081',
        access_key='AKIAIOSFODNN7EXAMPLE',
        secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    )


@pytest.mark.integration
def test_connection(intgr_config):
    with Session(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/')
        with request.fetch() as resp:
            assert 'version' in resp.json()


@pytest.mark.integration
def test_not_found(intgr_config):
    with Session(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/invalid-url-wow')
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 404
        request = Request(sess, 'GET', '/auth/uh-oh')
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_connection(intgr_config):
    async with AsyncSession(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/')
        async with request.fetch() as resp:
            assert 'version' in await resp.json()


@pytest.mark.integration
def test_auth(intgr_config):
    random_msg = uuid.uuid4().hex
    with Session(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/auth')
        request.set_json({
            'echo': random_msg,
        })
        with request.fetch() as resp:
            assert resp.status == 200
            data = resp.json()
            assert data['authorized'] == 'yes'
            assert data['echo'] == random_msg


@pytest.mark.integration
def test_auth_missing_signature(intgr_config, monkeypatch):
    random_msg = uuid.uuid4().hex
    with Session(config=intgr_config) as sess:
        rqst = Request(sess, 'GET', '/auth')
        rqst.set_json({
            'echo': random_msg,
        })
        # let it bypass actual signing
        from ai.backend.client import request
        noop_sign = lambda *args, **kwargs: ({}, None)
        monkeypatch.setattr(request, 'generate_signature', noop_sign)
        with pytest.raises(BackendAPIError) as e:
            with rqst.fetch():
                pass
        assert e.value.status == 401


@pytest.mark.integration
def test_auth_malformed(intgr_config):
    with Session(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/auth')
        request.set_content(
            b'<this is not json>',
            content_type='application/json',
        )
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 400


@pytest.mark.integration
def test_auth_missing_body(intgr_config):
    with Session(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/auth')
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_auth(intgr_config):
    random_msg = uuid.uuid4().hex
    async with AsyncSession(config=intgr_config) as sess:
        request = Request(sess, 'GET', '/auth')
        request.set_json({
            'echo': random_msg,
        })
        async with request.fetch() as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data['authorized'] == 'yes'
            assert data['echo'] == random_msg


@pytest.mark.integration
def test_kernel_lifecycles(intgr_config):
    with Session(config=intgr_config) as sess:
        kernel = sess.Kernel.get_or_create('python:latest')
        kernel_id = kernel.kernel_id
        info = kernel.get_info()
        # the tag may be different depending on alias/metadata config.
        lang = info['lang']
        assert lang.startswith('python:') or lang.startswith('lablup/python:')
        assert info['numQueriesExecuted'] == 1
        info = kernel.get_info()
        assert info['numQueriesExecuted'] == 2
        kernel.destroy()
        # kernel destruction is no longer synchronous!
        time.sleep(2.0)
        with pytest.raises(BackendAPIError) as e:
            info = sess.Kernel(kernel_id).get_info()
        assert e.value.status == 404


@pytest.yield_fixture
def py3_kernel(intgr_config):
    with Session(config=intgr_config) as sess:
        kernel = sess.Kernel.get_or_create('python:latest')
        yield kernel
        kernel.destroy()


def exec_loop(kernel, code):
    # The server may return continuation if kernel preparation
    # takes a little longer time (a few seconds).
    console = []
    num_queries = 0
    run_id = token_hex(8)
    while True:
        result = kernel.execute(run_id, code if num_queries == 0 else '')
        num_queries += 1
        console.extend(result['console'])
        if result['status'] == 'finished':
            break
    return aggregate_console(console), num_queries


@pytest.mark.integration
def test_kernel_execution(py3_kernel):
    console, n = exec_loop(py3_kernel, 'print("hello world"); raise RuntimeError()')
    assert 'hello world' in console['stdout']
    assert 'RuntimeError' in console['stderr']
    assert len(console['media']) == 0
    info = py3_kernel.get_info()
    assert info['numQueriesExecuted'] == n + 1


@pytest.mark.integration
def test_kernel_restart(py3_kernel):
    num_queries = 1  # first query is done by py3_kernel fixture (creation)
    first_code = textwrap.dedent('''
    a = "first"
    with open("test.txt", "w") as f:
        f.write("helloo?")
    print(a)
    ''').strip()
    second_code_name_error = textwrap.dedent('''
    print(a)
    ''').strip()
    second_code_file_check = textwrap.dedent('''
    with open("test.txt", "r") as f:
        print(f.read())
    ''').strip()
    console, n = exec_loop(py3_kernel, first_code)
    num_queries += n
    assert 'first' in console['stdout']
    assert console['stderr'] == ''
    assert len(console['media']) == 0
    py3_kernel.restart()
    num_queries += 1
    console, n = exec_loop(py3_kernel, second_code_name_error)
    num_queries += n
    assert 'NameError' in console['stderr']
    assert len(console['media']) == 0
    console, n = exec_loop(py3_kernel, second_code_file_check)
    num_queries += n
    assert 'helloo?' in console['stdout']
    assert console['stderr'] == ''
    assert len(console['media']) == 0
    info = py3_kernel.get_info()
    # FIXME: this varies between 2~4
    assert info['numQueriesExecuted'] == num_queries


@pytest.mark.integration
def test_admin_api(py3_kernel):
    sess = py3_kernel.session
    q = '''
    query($ak: String!) {
        compute_sessions(access_key: $ak, status: "RUNNING") {
            lang
        }
    }'''
    resp = sess.Admin.query(q, {
        'ak': sess.config.access_key,
    })
    assert 'compute_sessions' in resp
    assert len(resp['compute_sessions']) >= 1
    lang = resp['compute_sessions'][0]['lang']
    assert lang.startswith('python:') or lang.startswith('lablup/python:')
