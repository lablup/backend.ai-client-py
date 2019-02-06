import os
from yarl import URL
from typing import Any, Callable, Iterable, Tuple, Union

__all__ = [
    'get_config',
    'set_config',
    'APIConfig',
]

_config = None


def get_env(key: str,
            default: Any = None,
            clean: Callable[[str], Any] = lambda v: v):
    '''
    Retrieves a configuration value from the environment variables.
    The given *key* is uppercased and prefixed by ``"BACKEND_"`` and then
    ``"SORNA_"`` if the former does not exist.

    :param key: The key name.
    :param default: The default value returned when there is no corresponding
        environment variable.
    :param clean: A single-argument function that is applied to the result of lookup
        (in both successes and the default value for failures).
        The default is returning the value as-is.

    :returns: The value processed by the *clean* function.
    '''
    key = key.upper()
    v = os.environ.get('BACKEND_' + key)
    if v is None:
        v = os.environ.get('SORNA_' + key)
    if v is None:
        if default is None:
            raise KeyError(key)
        v = default
    return clean(v)


def bool_env(v: str) -> bool:
    v = v.lower()
    if v in ('y', 'yes', 't', 'true', '1'):
        return True
    if v in ('n', 'no', 'f', 'false', '0'):
        return False
    raise ValueError('Unrecognized value of boolean environment variable', v)


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
    '''
    Represents a set of API client configurations.
    The access key and secret key are mandatory -- they must be set in either
    environment variables or as the explicit arguments.

    :param endpoint: The URL prefix to make API requests via HTTP/HTTPS.
    :param version: The API protocol version.
    :param user_agent: A custom user-agent string which is sent to the API
        server as a ``User-Agent`` HTTP header.
    :param access_key: The API access key.
    :param secret_key: The API secret key.
    :param hash_type: The hash type to generate per-request authentication
        signatures.
    :param vfolder_mounts: A list of vfolder names (that must belong to the given
        access key) to be automatically mounted upon any
        :func:`Kernel.get_or_create()
        <ai.backend.client.kernel.Kernel.get_or_create>` calls.
    '''

    DEFAULTS = {
        'endpoint': 'https://api.backend.ai',
        'version': 'v4.20190315',
        'hash_type': 'sha256',
    }
    '''
    The default values except the access and secret keys.
    '''

    def __init__(self, *,
                 endpoint: Union[URL, str] = None,
                 version: str = None,
                 user_agent: str = None,
                 access_key: str = None,
                 secret_key: str = None,
                 hash_type: str = None,
                 vfolder_mounts: Iterable[str] = None,
                 skip_sslcert_validation: bool = None) -> None:
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
        arg_vfolders = set(vfolder_mounts) if vfolder_mounts else set()
        env_vfolders = set(get_env('VFOLDER_MOUNTS', [], clean=_clean_tokens))
        self._vfolder_mounts = [*(arg_vfolders | env_vfolders)]
        # prefer the argument flag and fallback to env if the flag is not set.
        self._skip_sslcert_validation = (skip_sslcert_validation
             if skip_sslcert_validation else
             get_env('SKIP_SSLCERT_VALIDATION', default='no', clean=bool_env))

    @property
    def endpoint(self) -> URL:
        '''The configured endpoint URL prefix.'''
        return self._endpoint

    @property
    def user_agent(self) -> str:
        '''The configured user agent string.'''
        return self._user_agent

    @property
    def access_key(self) -> str:
        '''The configured API access key.'''
        return self._access_key

    @property
    def secret_key(self) -> str:
        '''The configured API secret key.'''
        return self._secret_key

    @property
    def version(self) -> str:
        '''The configured API protocol version.'''
        return self._version

    @property
    def hash_type(self) -> str:
        '''The configured hash algorithm for API authentication signatures.'''
        return self._hash_type

    @property
    def vfolder_mounts(self) -> Tuple[str, ...]:
        '''The configured auto-mounted vfolder list.'''
        return self._vfolder_mounts

    @property
    def skip_sslcert_validation(self) -> bool:
        '''Whether to skip SSL certificate validation for the API gateway.'''
        return self._skip_sslcert_validation


def get_config():
    '''
    Returns the configuration for the current process.
    If there is no explicitly set :class:`APIConfig` instance,
    it will generate a new one from the current environment variables
    and defaults.
    '''
    global _config
    if _config is None:
        _config = APIConfig()
    return _config


def set_config(conf: APIConfig):
    '''
    Sets the configuration used throughout the current process.
    '''
    global _config
    _config = conf
