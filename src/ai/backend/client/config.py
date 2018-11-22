import os
from yarl import URL
from typing import Iterable, Tuple, Union

__all__ = [
    'APIConfig',
]

_config = None


def get_env(name, default=None, clean=lambda v: v):
    v = os.environ.get('BACKEND_' + name)
    if v is None:
        v = os.environ.get('SORNA_' + name)
    if v is None:
        if default is None:
            raise KeyError(name)
        v = default
    return clean(v)


def _clean_url(v):
    v = v if isinstance(v, URL) else URL(v)
    if not v.is_absolute():
        raise ValueError('URL must be absolute.')
    return v


def _clean_tokens(v):
    if isinstance(v, str):
        if not v:
            return tuple()
        return tuple(v.split(','))
    return tuple(iter(v))


class APIConfig:

    DEFAULTS = {
        'endpoint': 'https://api.backend.ai',
        'version': 'v4.20181215',
        'hash_type': 'sha256',
        'vfolder_mounts': [],
    }

    def __init__(self, *,
                 endpoint: Union[URL, str] = None,
                 version: str = None,
                 user_agent: str = None,
                 access_key: str = None,
                 secret_key: str = None,
                 hash_type: str = None,
                 vfolder_mounts: Iterable[str] = None) -> None:
        from . import get_user_agent  # noqa; to avoid circular imports
        self._endpoint = (
            _clean_url(endpoint) if endpoint else
            get_env('ENDPOINT', self.DEFAULTS['endpoint'], clean=_clean_url))
        self._version = version if version else self.DEFAULTS['version']
        self._user_agent = user_agent if user_agent else get_user_agent()
        self._access_key = access_key if access_key else get_env('ACCESS_KEY')
        self._secret_key = secret_key if secret_key else get_env('SECRET_KEY')
        self._hash_type = hash_type.lower() if hash_type else \
                          self.DEFAULTS['hash_type']
        self._vfolder_mounts = (
            _clean_tokens(vfolder_mounts) if vfolder_mounts else
            get_env('VFOLDER_MOUNTS', self.DEFAULTS['vfolder_mounts'],
                    clean=_clean_tokens))

    @property
    def endpoint(self) -> URL:
        return self._endpoint

    @property
    def user_agent(self) -> str:
        return self._user_agent

    @property
    def access_key(self) -> str:
        return self._access_key

    @property
    def secret_key(self) -> str:
        return self._secret_key

    @property
    def version(self) -> str:
        return self._version

    @property
    def hash_type(self) -> str:
        return self._hash_type

    @property
    def vfolder_mounts(self) -> Tuple[str, ...]:
        return self._vfolder_mounts


def get_config():
    global _config
    if _config is None:
        _config = APIConfig()
    return _config


def set_config(conf: APIConfig):
    global _config
    _config = conf
