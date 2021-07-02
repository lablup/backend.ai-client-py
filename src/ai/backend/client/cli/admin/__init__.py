from ..main import main


@main.group()
def admin():
    """
    Provides the admin API access.
    """


from . import (  # noqa
    agent,
    domain,
    etcd,
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
