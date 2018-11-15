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
def dummy_endpoint(defconfig):
    return str(defconfig.endpoint) + '/'
