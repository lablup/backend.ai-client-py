from __future__ import annotations
from typing import Optional, Union

from tqdm import tqdm

from .types import BaseProgressReporter

class TqdmProgressReporter(BaseProgressReporter):

    def __init__(
        self,
        tqdm: Optional[tqdm] = None
    ) -> None:
        self._tqdm_inst = tqdm
        
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        if self._tqdm_inst is not None:
            self._tqdm_inst.close()

    def update(
        self,
        *,
        desc: Optional[str] = None,
        total: Union[int, float, None] = None,
        progress: Union[int, float, None] = None,
    ) -> None:
        if self._tqdm_inst is None:
            return
        if desc is not None:
            self._tqdm_inst.desc = desc
        if total is not None:
            self._tqdm_inst.total = total
        if progress is not None:
            self._tqdm_inst.update(progress)
