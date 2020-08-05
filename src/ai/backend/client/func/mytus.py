from aiotusclient import client

import asyncio
from ai.backend.client.request import Request
from ai.backend.client.session import AsyncSession


from datetime import datetime
from dateutil.tz import tzutc
from ai.backend.client.auth import generate_signature
from ai.backend.client.session import Session
import sys

from pathlib import Path


def request():
    """
    async with AsyncSession() as sess:

        rqst = Request(sess, 'POST', '/folders/mydata1/upload')
        async with rqst.fetch() as resp:
            print(await resp.text())
    
    """
    base_dir = None
    name = "mydata1"
    filenames = ['image.py']
    if base_dir is None:
        base_dir = Path.cwd()
    with Session() as session:
        try:
            session.VFolder(name).upload(
                filenames,
                basedir=base_dir,
            )
            print('Done.')
        except Exception as e:
            print(e)
            sys.exit(1)
    
def main():
    request()


if __name__ == "__main__":
    main()