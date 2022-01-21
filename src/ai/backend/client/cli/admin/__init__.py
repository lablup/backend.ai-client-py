from ..main import main


@main.group()
def admin():
    """
    Administrative command set
    """


from . import manager  # noqa
from . import (
    agent,
    domain,
    etcd,
    filebrowser,
    group,
    image,
    keypair,
    license,
    resource,
    resource_policy,
    scaling_group,
    session,
    storage,
    user,
    vfolder,
)
