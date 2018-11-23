'''
A compatibility module for backported codes from Python 3.6 standard library.
'''

import asyncio
import binascii
import os


def token_bytes(nbytes=None):
    '''
    Emulation of secrets.token_bytes()
    '''
    if nbytes is None:
        nbytes = 32
    return os.urandom(nbytes)


def token_hex(nbytes=None):
    '''
    Emulation of secrets.token_hex()
    '''
    return binascii.hexlify(token_bytes(nbytes)).decode('ascii')


if hasattr(asyncio, 'get_running_loop'):
    current_loop = asyncio.get_running_loop
else:
    current_loop = asyncio.get_event_loop
