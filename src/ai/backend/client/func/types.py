from __future__ import annotations

from collections import UserDict
from typing import (
    Any,
    Generic,
    Mapping,
    Sequence,
    TypeVar,
)

import attr

_predefined_humanized_field_names = {
    "id": "ID",
    "uuid": "UUID",
    "group_id": "Group ID",
    "user_id": "User ID",
    "resource_policy": "Res.Policy",
    "concurrency_used": "Concur.Used",
    "fsprefix": "FS Prefix",
    "hardware_metadata": "HW Metadata",
    "performance_metric": "Perf.Metric",
}


def _make_camel_case(name: str) -> str:
    return " ".join(
        map(lambda s: s[0].upper() + s[1:], name.split("_")),
    )


@attr.define(slots=True, frozen=True)
class FieldSpec:
    """
    The specification on how to represent a GraphQL object field
    in the functional API handlers.

    Attributes:
        field_ref: The string to be interpolated inside GraphQL queries.
            It may contain sub-fields if the queried field supports.
        humanized_name: The string to be shown as the field name by the console formatter.
            If not set, it's auto-generated from field_name by camel-casing it and checking
            a predefined humanization mapping.
        field_name: The exact field name slug.  If not set, it's taken from field_ref.
        alt_name: The field name slug to refer the field inside a FieldSet object hosting
            this FieldSpec instance.
        subfields: A FieldSet instance to represent sub-fields in the GraphQL schema.
            If set, field_ref is Automatically updated to have the braced subfield list
            for actual GraphQL queries.
    """

    field_ref: str = attr.field()
    humanized_name: str = attr.field()
    field_name: str = attr.field()
    alt_name: str = attr.field()
    formatter: Any = attr.field(default=None)
    subfields: FieldSet = attr.field(factory=lambda: FieldSet([]))

    def __attrs_post_init__(self) -> None:
        if self.subfields:
            subfields = " ".join(f.field_ref for f in self.subfields.values())
            object.__setattr__(self, 'field_ref', f"{self.field_name} {{ {subfields} }}")

    @humanized_name.default
    def _autogen_humanized_name(self) -> str:
        # to handle cases like "groups { id name }", "user_info { full_name }"
        field_name = self.field_ref.partition(" ")[0]
        if h := _predefined_humanized_field_names.get(field_name):
            return h
        if field_name.startswith("is_"):
            return _make_camel_case(field_name[3:]) + "?"
        return _make_camel_case(field_name)

    @field_name.default
    def _default_field_name(self) -> str:
        return self.field_ref.partition(" ")[0]

    @alt_name.default
    def _default_alt_name(self) -> str:
        return self.field_ref.partition(" ")[0]


class FieldSet(UserDict, Mapping[str, FieldSpec]):

    def __init__(self, fields: Sequence[FieldSpec]) -> None:
        super().__init__({
            f.alt_name: f for f in fields
        })


T = TypeVar('T')


@attr.define(slots=True)
class PaginatedResult(Generic[T]):
    total_count: int
    items: Sequence[T]
    fields: Sequence[FieldSpec]
