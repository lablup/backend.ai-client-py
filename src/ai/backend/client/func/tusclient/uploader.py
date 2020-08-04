from typing import Optional
import asyncio
from urllib.parse import urljoin
import time
import requests
import aiohttp
from tqdm import tqdm
from .baseuploader import BaseUploader

from .exceptions import TusUploadFailed, TusCommunicationError
from .request import TusRequest, AsyncTusRequest, catch_requests_error


def _verify_upload(request: TusRequest):
    if request.status_code == 204:
        return True
    else:
        raise TusUploadFailed('', request.status_code,
                              request.response_content)


class Uploader(BaseUploader):
    def upload(self, stop_at: Optional[int] = None):
        """
        Perform file upload.

        Performs continous upload of chunks of the file. The size uploaded at
        each cycle is
        the value of the attribute 'chunk_size'.

        :Args:
            - stop_at (Optional[int]):
                Determines at what offset value the upload should stop.
                If not specified this
                defaults to the file size.
        """
        self.stop_at = stop_at or self.get_file_size()

        while self.offset < self.stop_at:
            self.upload_chunk()

    def upload_chunk(self):
        """
        Upload chunk of file.
        """
        self._retried = 0
        if not self.url:
            self.set_url(self.create_url())
            self.offset = 0
        self._do_request()
        self.offset = int(self.request.response_headers.get('upload-offset'))

    @catch_requests_error
    def create_url(self):
        """
        Return upload url.

        Makes request to tus server to create a new upload url for the
        required file upload.
        """
        resp = requests.post(
            self.client.url, headers=self.get_url_creation_headers())
        url = resp.headers.get("location")
        if url is None:
            msg = 'Attempt to retrieve create file url with status {}'.format(
                resp.status_code)
            raise TusCommunicationError(msg, resp.status_code, resp.content)
        return urljoin(self.client.url, url)

    def _do_request(self):
        self.request = TusRequest(self)
        try:
            self.request.perform()
            _verify_upload(self.request)
        except TusUploadFailed as error:
            self._retry_or_cry(error)

    def _retry_or_cry(self, error):
        print("Retry error ", error)
        if self.retries > self._retried:
            time.sleep(self.retry_delay)

            self._retried += 1
            try:
                self.offset = self.get_offset()
            except TusCommunicationError as err:
                self._retry_or_cry(err)
            else:
                self._do_request()
        else:
            raise error


class AsyncUploader(BaseUploader):
    def __init__(self, *args,
                 io_loop: Optional[asyncio.AbstractEventLoop] = None,
                 **kwargs):
        self.io_loop = io_loop
        super().__init__(*args, **kwargs)

    async def upload(self, stop_at: Optional[int] = None):
        """
        Perform file upload.

        Performs continous upload of chunks of the file. The size uploaded at each cycle is
        the value of the attribute 'chunk_size'.

        :Args:
            - stop_at (Optional[int]):
                Determines at what offset value the upload should stop. If not specified this
                defaults to the file size.
        """
        self.stop_at = stop_at or self.get_file_size()
        no_chunks = self.get_file_size() // self.chunk_size
        print("File size: ", self.get_file_size(), "bytes; Total number of chunks: ", no_chunks)

        with tqdm(total=no_chunks) as pbar:
            while self.offset < self.stop_at:
                await self.upload_chunk()
                pbar.update(1)

    async def upload_chunk(self):
        """
        Upload chunk of file.
        """
        self._retried = 0
        if not self.url:
            self.set_url(await self.create_url())
            self.offset = 0
        await self._do_request()
        self.offset = int(self.request.response_headers.get('upload-offset'))

    async def create_url(self):
        """
        Return upload url.

        Makes request to tus server to create a new upload url for the
        required file upload.
        """
        try:
            async with aiohttp.ClientSession(loop=self.io_loop) as session:
                headers = self.get_url_creation_headers()
                params = self.client.params
                params['size'] = int(params['size'])
                async with session.post(self.client.session_create_url,
                                        headers=headers,
                                        params=params) as resp:
                    url = jwt_token = await resp.json()
                    jwt_token = jwt_token['token']
                    url = self.client.session_upload_url + jwt_token
                    if url is None:
                        msg = 'Attempt to retrieve create file url with \
                                status {}'.format(resp.status)
                        raise TusCommunicationError(msg,
                                                    resp.status,
                                                    await resp.content.read()
                                                    )
                    return url
        except aiohttp.ClientError as error:
            raise TusCommunicationError(error)

    async def _do_request(self):
        self.request = AsyncTusRequest(self)
        try:
            await self.request.perform()
            _verify_upload(self.request)
        except TusUploadFailed as error:
            await self._retry_or_cry(error)

    async def _retry_or_cry(self, error):
        print("Error ", error)
        print("Retries ", self.retries, self._retried)
        if self.retries > self._retried:
            await asyncio.sleep(self.retry_delay, loop=self.io_loop)

            self._retried += 1
            try:
                self.offset = self.get_offset()
            except TusCommunicationError as err:
                await self._retry_or_cry(err)
            else:
                await self._do_request()
        else:
            print("Error ", error)
            raise error
