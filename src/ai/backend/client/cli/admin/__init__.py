from ..main import main


@main.group()
def admin():
    """
    Administrative command set
    """


from . import (
    agent,
    domain,
    etcd,
    filebrowser,
    group,
    image,
    keypair,
    license,
    manager,  # noqa
    resource,
    resource_policy,
    scaling_group,
    session,
    storage,
    user,
    vfolder,
)
