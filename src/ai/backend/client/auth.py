import enum
import hashlib
import hmac

import attr

from .base import api_function

__all__ = (
    'Auth',
    'AuthToken',
    'AuthTokenTypes',
    'generate_signature',
)


class AuthTokenTypes(enum.Enum):
    KEYPAIR = 'keypair'
    JWT = 'jwt'


@attr.s
class AuthToken:
    type = attr.ib(default=AuthTokenTypes.KEYPAIR)  # type: AuthTokenTypes
    content = attr.ib(default=None)                 # type: str


def generate_signature(method, version, endpoint,
                       date, rel_url, content_type, content,
                       access_key, secret_key, hash_type):
    '''
    Generates the API request signature from the given parameters.
    '''
    hash_type = hash_type
    hostname = endpoint._val.netloc  # FIXME: migrate to public API
    if version >= 'v4.20181215':
        content = b''
    else:
        if content_type.startswith('multipart/'):
            content = b''
    body_hash = hashlib.new(hash_type, content).hexdigest()

    sign_str = '{}\n{}\n{}\nhost:{}\ncontent-type:{}\nx-backendai-version:{}\n{}'.format(  # noqa
        method.upper(),
        rel_url,
        date.isoformat(),
        hostname,
        content_type.lower(),
        version,
        body_hash
    )
    sign_bytes = sign_str.encode()

    sign_key = hmac.new(secret_key.encode(),
                        date.strftime('%Y%m%d').encode(), hash_type).digest()
    sign_key = hmac.new(sign_key, hostname.encode(), hash_type).digest()

    signature = hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
    headers = {
        'Authorization': 'BackendAI signMethod=HMAC-{}, credential={}:{}'.format(
            hash_type.upper(),
            access_key,
            signature
        ),
    }
    return headers, signature


class Auth:
    '''
    Provides the function interface for login session management and authorization.
    '''

    @api_function
    @classmethod
    async def login(cls, user_id: str, password: str):
        from .request import Request
        rqst = Request(cls.session, 'POST', '/server/login')
        rqst.set_json({
            'username': user_id,
            'password': password,
        })
        async with rqst.fetch(anonymous=True) as resp:
            data = await resp.json()
            data['cookies'] = resp.raw_response.cookies
            return data

    @api_function
    @classmethod
    async def logout(cls):
        from .request import Request
        rqst = Request(cls.session, 'POST', '/server/logout')
        async with rqst.fetch() as resp:
            resp.raw_response.raise_for_status()
