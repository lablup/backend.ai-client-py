from __future__ import annotations

import sys

import click
import humanize
from tabulate import tabulate

from ai.backend.client.func.vfolder import _default_list_fields
from ai.backend.client.session import Session

from ..pretty import print_error
from ..types import CLIContext
from ..vfolder import vfolder as user_vfolder
from . import admin


@admin.group()
def filebrowser() -> None:
    """
    FileBrowser administration commands.
    """
