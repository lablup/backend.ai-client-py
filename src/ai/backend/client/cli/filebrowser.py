from datetime import datetime
import json
from pathlib import Path
import sys

import click
import humanize
from tabulate import tabulate

from ai.backend.client.config import DEFAULT_CHUNK_SIZE
from ai.backend.client.session import Session
from .main import main
from .interaction import ask_yn
from .pretty import print_done, print_error, print_fail, print_info, print_wait
from .params import ByteSizeParamType, ByteSizeParamCheckType


@main.group()
def filebrowser():
    """Set of filebrowser operations"""


@filebrowser.command()
@click.argument('vfolders', type=str)
def create(vfolders):
    """ Create or update filebrowser session

    \b
    vfolders: List of virtual folders to add to FileBrowser session.
    """
    with Session() as session:
        try:
            print("Trying")
            print(vfolders)
            session.FileBrowser.create_or_update_browser()
        except Exception as e:
            print("my error ")
            print_error(e)
            sys.exit(1)
