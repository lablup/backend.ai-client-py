import enum
import hashlib
import hmac

import attr

__all__ = (
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
