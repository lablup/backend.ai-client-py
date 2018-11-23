import pytest

from ai.backend.client.config import APIConfig, set_config


@pytest.fixture(autouse=True)
def defconfig():
    c = APIConfig(endpoint='http://127.0.0.1:8081',
                  access_key='AKIAIOSFODNN7EXAMPLE',
                  secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')
    set_config(c)
    return c


@pytest.fixture
def example_keypair():
    return ('AKIAIOSFODNN7EXAMPLE', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')


@pytest.fixture
def dummy_endpoint(defconfig):
    return str(defconfig.endpoint) + '/'


@pytest.fixture
def dummy_endpoint_versioned(defconfig):
    return str(defconfig.endpoint) + '/v4/'
