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
@click.argument('scaling_group', metavar='SCALING_GROUP', default="default")
@click.argument('group', metavar='GROUP', default="default")
@click.option('-a', '--all', 'all_', is_flag=True,
              help="Get all resources of group.")
def check(scaling_group: str, group: str, all_: bool) -> None:
    """
    Get available resources from the scaling groups.
    """
    try:
        with Session() as session:
            ret = session.Resource.get_available_resources(scaling_group, group)
            slot_types = session.Resource.get_resource_slots()

            print(f"Total remaining resources of scaling group [{scaling_group}]:")
            prefix = "- "
            print_resource(ret["scaling_group_remaining"], slot_types, prefix=prefix, nan_as_infinite=True)

            print("Each resources of scaling groups:")
            if not all_:
                print(f"  [{scaling_group}]")
                print("    Using:")
                prefix = "    - "
                print_resource(ret["scaling_groups"][scaling_group]["using"], slot_types, prefix=prefix, nan_as_infinite=True)
                print("    Remaining:")
                print_resource(ret["scaling_groups"][scaling_group]["remaining"], slot_types, prefix=prefix, nan_as_infinite=True)
            else:
                for x in ret["scaling_groups"].keys():
                    print(f"  [{x}]")
                    print("    Using:")
                    prefix = "    - "
                    print_resource(ret["scaling_groups"][x]["using"], slot_types, prefix=prefix, nan_as_infinite=True)
                    print("    Remaining:")
                    print_resource(ret["scaling_groups"][x]["remaining"], slot_types, prefix=prefix, nan_as_infinite=True)

            print("Group limits:")
            prefix = "- "
            print_resource(ret["group_limits"], slot_types, prefix=prefix, nan_as_infinite=True)
            print("Group using:")
            print_resource(ret["group_using"], slot_types, prefix=prefix, nan_as_infinite=True)
            print("Group remaining:")
            print_resource(ret["group_remaining"], slot_types, prefix=prefix, nan_as_infinite=True)
    except Exception as e:
        print_error(e)
        sys.exit(1)