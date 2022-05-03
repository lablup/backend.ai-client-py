from ..main import main


@main.group()
def admin():
    """
    Administrative command set
    """


from . import (  # noqa
    agent,
    audit_logs,
    domain,
    etcd,
    group,
    image,
    keypair,
    manager,
    license,
    resource,
    resource_policy,
    scaling_group,
    session,
    storage,
    user,
    vfolder,
)
