import asyncio
from pathlib import Path
from typing import (
    Sequence,
    Union,
)

import aiohttp
import janus
from tqdm import tqdm

from yarl import URL
from aiotusclient import client

from ai.backend.client.output.fields import vfolder_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from .base import api_function, BaseFunction
from ..compat import current_loop
from ..config import DEFAULT_CHUNK_SIZE, MAX_INFLIGHT_CHUNKS
from ..pagination import generate_paginated_results
from ..request import Request

__all__ = (
    'FileBrowser',
)

class FileBrowser(BaseFunction):
    @api_function
    @classmethod

    async def create_or_update_browser(self):
        rqst = Request('POST', '/browser/create')
       
        print("DEBUG: ", rqst.config.vfolder_mounts,rqst.headers, rqst.path, rqst.params, rqst._build_url())
        rqst.headers['X-RateLimit-Limit'] = "1000"
        
        async with rqst.fetch() as resp:
            return await resp.text()
