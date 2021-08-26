import sys

import click

from . import main
from .pretty import print_error, print_resource
from ..session import Session


@main.group()
def resource():
    """
    Provides resource check operations
    """


@resource.command()
@click.argument('group', metavar='NAME', default="default")
def check_group(group: str) -> None:
    """
    Display the available resources from all allowed scaling groups of the given user group (project).
    """
    try:
        with Session() as session:
            ret = session.Resource.check_group(group)
            slot_types = session.Resource.get_resource_slots()
            print("Limits:")
            prefix = "- "
            print_resource(ret["limits"], slot_types, prefix=prefix, nan_as_infinite=True)
            print("Occupied:")
            print_resource(ret["occupied"], slot_types, prefix=prefix)
            print("Remaining:")
            print_resource(ret["remaining"], slot_types, prefix=prefix)
            print("Scaling groups allowed for this group:")
            for sgroup_name in ret["scaling_groups"].keys():
                print(f"  [{sgroup_name}]")
                print("    Occupied:")
                prefix = "    - "
                print_resource(ret["scaling_groups"][sgroup_name]["occupied"], slot_types, prefix=prefix)
                print("    Remaining:")
                print_resource(ret["scaling_groups"][sgroup_name]["remaining"], slot_types, prefix=prefix)
    except Exception as e:
        print_error(e)
        sys.exit(1)


@resource.command()
@click.argument('scaling_group', metavar='NAME', default="default")
def check_scaling_group(scaling_group: str) -> None:
    """
    Display the available resource from the given scaling group.
    """
    try:
        with Session() as session:
            ret = session.Resource.check_scaling_group(scaling_group)
            slot_types = session.Resource.get_resource_slots()
            print(f"Total remaining resources of scaling group [{scaling_group}]:")
            prefix = "- "
            print_resource(ret["remaining"], slot_types, prefix=prefix)
    except Exception as e:
        print_error(e)
        sys.exit(1)