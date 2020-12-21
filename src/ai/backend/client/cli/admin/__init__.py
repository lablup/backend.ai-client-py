from .. import main


@main.group()
def admin():
    '''
    Provides the admin API access.
    '''


def _attach_command():
    from . import (  # noqa
        agents,
        domains,
        etcd,
        groups,
        images,
        keypairs,
        license,
        resources,
        resource_policies,
        scaling_groups,
        sessions,
        storage,
        users,
        vfolders,
    )


_attach_command()
