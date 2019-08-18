from . import admin
from ...session import Session
from ..pretty import print_error


@admin.group()
def resources():
    '''
    Manage resources.
    (admin privilege required)
    '''


@resources.command()
def resource_slots():
    """
    Get available resource slots.
    """
    with Session() as session:
        try:
            ret = session.Resource.get_resource_slots()
            for key, value in ret.items():
                print(key, '(' + value + ')')
        except Exception as e:
            print_error(e)


@resources.command()
def vfolder_types():
    """
    Get available vfolder types.
    """
    with Session() as session:
        try:
            ret = session.Resource.get_vfolder_types()
            for t in ret:
                print(t)
        except Exception as e:
            print_error(e)


@resources.command()
def recalculate_usage():
    """
    Re-calculate resource occupation by sessions.

    Sometime, reported allocated resources is deviated from the actual value.
    By executing this command, the discrepancy will be corrected with real value.
    """
    with Session() as session:
        try:
            session.Resource.recalculate_usage()
            print('Resource allocation is re-calculated.')
        except Exception as e:
            print_error(e)
