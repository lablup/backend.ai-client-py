from __future__ import annotations

from .formatters import (
    AgentStatFormatter,
    GroupListFormatter,
    ContainerListFormatter,
    DependencyListFormatter,
    SubFieldOutputFormatter,
    KernelStatFormatter,
    nested_dict_formatter,
    mibytes_output_formatter,
    resource_slot_formatter
)
from .types import (
    FieldSet,
    FieldSpec,
)


agent_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('status'),
    FieldSpec('scaling_group'),
    FieldSpec('available_slots', formatter=resource_slot_formatter),
    FieldSpec('occupied_slots', formatter=resource_slot_formatter),
    FieldSpec('hardware_metadata', formatter=nested_dict_formatter),
    FieldSpec('live_stat', formatter=AgentStatFormatter()),
    FieldSpec('cpu_cur_pct', 'CPU Usage (%)'),
    FieldSpec('mem_cur_bytes', 'Used Memory (MiB)', formatter=mibytes_output_formatter),
    FieldSpec('addr'),
    FieldSpec('region'),
    FieldSpec('first_contact'),
    FieldSpec('cpu_cur_pct'),
    FieldSpec('mem_cur_bytes'),
])


keypair_fields = FieldSet([
    FieldSpec('user_id', "Email"),
    FieldSpec('user_info { full_name }', "Full Name", alt_name='full_name',
              formatter=SubFieldOutputFormatter("full_name")),
    FieldSpec('access_key'),
    FieldSpec('secret_key'),
    FieldSpec('is_active'),
    FieldSpec('is_admin'),
    FieldSpec('created_at'),
    FieldSpec('last_used'),
    FieldSpec('resource_policy'),
    FieldSpec('rate_limit'),
    FieldSpec('concurrency_limit'),
    FieldSpec('concurrency_used'),
])


user_fields = FieldSet([
    FieldSpec('uuid'),
    FieldSpec('role'),
    FieldSpec('username'),
    FieldSpec('email'),
    FieldSpec('need_password_change'),
    FieldSpec('is_active'),
    FieldSpec('status'),
    FieldSpec('status_info'),
    FieldSpec('created_at'),
    FieldSpec('domain_name'),
    FieldSpec('groups { id name }', formatter=GroupListFormatter()),
])


session_fields = FieldSet([
    FieldSpec('id', "Kernel ID", alt_name='kernel_id'),
    FieldSpec('name'),
    FieldSpec('type'),
    FieldSpec('session_id', "Session ID"),
    FieldSpec('status'),
    FieldSpec('status_info'),
    FieldSpec('status_data', formatter=nested_dict_formatter),
    FieldSpec('status_changed', "Last Updated"),
    FieldSpec('created_at'),
    FieldSpec('terminated_at'),
    FieldSpec('result'),
    FieldSpec('group_name', "Project/Group"),
    FieldSpec('access_key', "Owner"),
    FieldSpec('image'),
    FieldSpec('tag'),
    FieldSpec('occupied_slots', formatter=resource_slot_formatter),
    FieldSpec('cluster_hostname'),
    FieldSpec(
        'containers',
        subfields=FieldSet([
            FieldSpec('id'),
            FieldSpec('cluster_role'),
            FieldSpec('cluster_idx'),
            FieldSpec('cluster_hostname'),
            FieldSpec('agent'),
            FieldSpec('status'),
            FieldSpec('status_info'),
            FieldSpec('status_data', formatter=nested_dict_formatter),
            FieldSpec('status_changed'),
            FieldSpec('occupied_slots', formatter=resource_slot_formatter),
            FieldSpec('live_stat', formatter=KernelStatFormatter()),
            FieldSpec('last_stat', formatter=KernelStatFormatter()),
        ]),
        formatter=ContainerListFormatter(),
    ),
    FieldSpec(
        'dependencies { name id }',
        formatter=DependencyListFormatter(),
    ),
])

session_fields_v5 = FieldSet([
    FieldSpec(
        'containers',
        subfields=FieldSet([
            FieldSpec('id'),
            FieldSpec('role'),
            FieldSpec('agent'),
            FieldSpec('status'),
            FieldSpec('status_info'),
            FieldSpec('status_data', formatter=nested_dict_formatter),
            FieldSpec('status_changed'),
            FieldSpec('occupied_slots', formatter=resource_slot_formatter),
            FieldSpec('live_stat', formatter=KernelStatFormatter()),
            FieldSpec('last_stat', formatter=KernelStatFormatter()),
        ]),
        formatter=ContainerListFormatter(),
    )
])


vfolder_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('host'),
    FieldSpec('name'),
    FieldSpec('created_at'),
    FieldSpec('creator'),
    FieldSpec('group'),
    FieldSpec('permission'),
    FieldSpec('ownership_type'),
    FieldSpec('usage_mode'),
    FieldSpec('last_used'),
    FieldSpec('max_size'),
])


storage_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('backend'),
    FieldSpec('path'),
    FieldSpec('fsprefix'),
    FieldSpec('capabilities'),
    FieldSpec('hardware_metadata', formatter=nested_dict_formatter),
    FieldSpec('performance_metric', formatter=nested_dict_formatter),
])
