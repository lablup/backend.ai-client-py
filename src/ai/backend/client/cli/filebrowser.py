import sys

import click

from ai.backend.client.session import Session

from .main import main
from .pretty import print_error


@main.group()
def filebrowser():
    """Set of filebrowser operations"""


@filebrowser.command()
@click.option(
    "-v",
    "--vfolder",
    help="Vfolder to be attached for a filebrowser session",
    type=str,
    metavar="VFOLDER",
    multiple=True,
)
def create(vfolder):
    """Create or update filebrowser session"""
    vfolder = list(vfolder)

    with Session() as session:
        try:
            session.FileBrowser.create_or_update_browser(vfolder)
        except Exception as e:
            print_error(e)
            sys.exit(1)


@filebrowser.command()
@click.option(
    "-cid",
    "--container_id",
    help="Container ID of user filebrowser session.",
    type=str,
    metavar="CID",
)
def destroy(container_id):
    """Destroy filebrowser session using Container ID."""

    with Session() as session:
        try:
            session.FileBrowser.destroy_browser(container_id)
        except Exception as e:
            print_error(e)
            sys.exit(1)
