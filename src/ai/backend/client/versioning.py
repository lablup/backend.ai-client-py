from typing import (
    Callable, Union,
    Tuple, Sequence,
)


naming_profile = {
    'path': ('kernel', 'session'),
    'session_events_path': ('/stream/kernel/_/events', '/events/session'),
    'name_arg': ('clientSessionToken', 'name'),
    'event_name_arg': ('sessionId', 'name'),
    'name_gql_field': ('sess_id', 'name'),
    'type_gql_field': ('sess_type', 'type'),
}


def get_naming(api_version: Tuple[int, str], key: str) -> str:
    if api_version[0] <= 4:
        return naming_profile[key][0]
    return naming_profile[key][1]


def apply_version_aware_fields(
    api_session,
    fields: Sequence[Tuple[str, Union[Callable, str]]],
) -> Sequence[Tuple[str, str]]:
    version_aware_fields = []
    for f in fields:
        if callable(f[1]):
            version_aware_fields.append((f[0], f[1](api_session)))
        else:
            version_aware_fields.append((f[0], f[1]))
    return version_aware_fields
