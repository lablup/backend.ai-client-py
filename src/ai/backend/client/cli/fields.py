from __future__ import annotations

from typing import Sequence

from ..func.types import FieldSet
from ..output.formatters import (
    AgentStatFormatter,
    GroupListFormatter,
    ContainerListFormatter,
    DependencyListFormatter,
    SubFieldOutputFormatter,
    KernelStatFormatter,
    nested_dict_formatter,
    mibytes_output_formatter,
    resource_slot_formatter,
    sizebytes_output_formatter,
)
from ..output.types import CliFieldSpec


def set_default_fields(fields: FieldSet, names: Sequence[str]) -> Sequence[CliFieldSpec]:
    return tuple(fields[name] for name in names)


container_fields = FieldSet([
    CliFieldSpec('id', "Kernel ID", alt_name='kernel_id'),
    CliFieldSpec('cluster_role'),
    CliFieldSpec('cluster_idx'),
    CliFieldSpec('cluster_hostname'),
    CliFieldSpec('session_id', "Session ID"),
    CliFieldSpec('image'),
    CliFieldSpec('registry'),
    CliFieldSpec('status'),
    CliFieldSpec('status_info'),
    CliFieldSpec('status_data', formatter=nested_dict_formatter),
    CliFieldSpec('status_changed'),
    CliFieldSpec('agent'),
    CliFieldSpec('container_id'),
    CliFieldSpec('resource_opts', formatter=nested_dict_formatter),
    CliFieldSpec('occupied_slots', formatter=resource_slot_formatter),
    CliFieldSpec('live_stat', formatter=KernelStatFormatter()),
    CliFieldSpec('last_stat', formatter=KernelStatFormatter()),
])


agent_fields = FieldSet([
    CliFieldSpec('id'),
    CliFieldSpec('status'),
    CliFieldSpec('status_changed'),
    CliFieldSpec('region'),
    CliFieldSpec('architecture'),
    CliFieldSpec('scaling_group'),
    CliFieldSpec('schedulable'),
    CliFieldSpec('available_slots', formatter=resource_slot_formatter),
    CliFieldSpec('occupied_slots', formatter=resource_slot_formatter),
    CliFieldSpec('addr'),
    CliFieldSpec('first_contact'),
    CliFieldSpec('lost_at'),
    CliFieldSpec('live_stat', formatter=AgentStatFormatter()),
    CliFieldSpec('version'),
    CliFieldSpec('compute_plugins'),
    CliFieldSpec('hardware_metadata', formatter=nested_dict_formatter),
    CliFieldSpec('compute_containers', subfields=container_fields,
              formatter=ContainerListFormatter()),
    # legacy fields
    CliFieldSpec('cpu_cur_pct', 'CPU Usage (%)'),
    CliFieldSpec('mem_cur_bytes', 'Used Memory (MiB)', formatter=mibytes_output_formatter),
])

domain_fields = FieldSet([
    CliFieldSpec('name'),
    CliFieldSpec('description'),
    CliFieldSpec('is_active'),
    CliFieldSpec('created_at'),
    CliFieldSpec('total_resource_slots', formatter=resource_slot_formatter),
    CliFieldSpec('allowed_vfolder_hosts'),
    CliFieldSpec('allowed_docker_registries'),
    CliFieldSpec('integration_id'),
])

group_fields = FieldSet([
    CliFieldSpec('id'),
    CliFieldSpec('name'),
    CliFieldSpec('description'),
    CliFieldSpec('is_active'),
    CliFieldSpec('created_at'),
    CliFieldSpec('domain_name'),
    CliFieldSpec('total_resource_slots', formatter=resource_slot_formatter),
    CliFieldSpec('allowed_vfolder_hosts'),
    CliFieldSpec('integration_id'),
])


image_fields = FieldSet([
    CliFieldSpec('name'),
    CliFieldSpec('registry'),
    CliFieldSpec('architecture'),
    CliFieldSpec('tag'),
    CliFieldSpec('digest'),
    CliFieldSpec('size_bytes', formatter=sizebytes_output_formatter),
    CliFieldSpec('aliases'),
])


keypair_fields = FieldSet([
    CliFieldSpec('user_id', "Email"),
    CliFieldSpec('user_info { full_name }', "Full Name", alt_name='full_name',
              formatter=SubFieldOutputFormatter("full_name")),
    CliFieldSpec('access_key'),
    CliFieldSpec('secret_key'),
    CliFieldSpec('is_active'),
    CliFieldSpec('is_admin'),
    CliFieldSpec('created_at'),
    CliFieldSpec('modified_at'),
    CliFieldSpec('last_used'),
    CliFieldSpec('resource_policy'),
    CliFieldSpec('rate_limit'),
    CliFieldSpec('concurrency_used'),
    CliFieldSpec('ssh_public_key'),
    CliFieldSpec('ssh_private_key'),
    CliFieldSpec('dotfiles'),
    CliFieldSpec('bootstrap_script'),
])


keypair_resource_policy_fields = FieldSet([
    CliFieldSpec('name'),
    CliFieldSpec('created_at'),
    CliFieldSpec('total_resource_slots'),
    CliFieldSpec('max_concurrent_sessions'),  # formerly concurrency_limit
    CliFieldSpec('max_vfolder_count'),
    CliFieldSpec('max_vfolder_size', formatter=sizebytes_output_formatter),
    CliFieldSpec('idle_timeout'),
    CliFieldSpec('max_containers_per_session'),
    CliFieldSpec('allowed_vfolder_hosts'),
])


scaling_group_fields = FieldSet([
    CliFieldSpec('name'),
    CliFieldSpec('description'),
    CliFieldSpec('is_active'),
    CliFieldSpec('created_at'),
    CliFieldSpec('driver'),
    CliFieldSpec('driver_opts', formatter=nested_dict_formatter),
    CliFieldSpec('scheduler'),
    CliFieldSpec('scheduler_opts', formatter=nested_dict_formatter),
])


session_fields = FieldSet([
    CliFieldSpec('id', "Kernel ID", alt_name='kernel_id'),
    CliFieldSpec('tag'),
    CliFieldSpec('name'),
    CliFieldSpec('type'),
    CliFieldSpec('session_id', "Session ID"),
    CliFieldSpec('image'),
    CliFieldSpec('registry'),
    CliFieldSpec('cluster_template'),
    CliFieldSpec('cluster_mode'),
    CliFieldSpec('cluster_size'),
    CliFieldSpec('domain_name'),
    CliFieldSpec('group_name', "Project/Group"),
    CliFieldSpec('group_id'),
    CliFieldSpec('user_email'),
    CliFieldSpec('user_id'),
    CliFieldSpec('access_key', "Owner Access Key"),
    CliFieldSpec('created_user_email'),
    CliFieldSpec('created_user_id'),
    CliFieldSpec('status'),
    CliFieldSpec('status_info'),
    CliFieldSpec('status_data', formatter=nested_dict_formatter),
    CliFieldSpec('status_changed', "Last Updated"),
    CliFieldSpec('created_at'),
    CliFieldSpec('terminated_at'),
    CliFieldSpec('starts_at'),
    CliFieldSpec('startup_command'),
    CliFieldSpec('result'),
    CliFieldSpec('resoucre_opts', formatter=nested_dict_formatter),
    CliFieldSpec('scaling_group'),
    CliFieldSpec('service_ports', formatter=nested_dict_formatter),
    CliFieldSpec('mounts'),
    CliFieldSpec('occupied_slots', formatter=resource_slot_formatter),
    CliFieldSpec(
        'containers',
        subfields=container_fields,
        formatter=ContainerListFormatter(),
    ),
    CliFieldSpec(
        'dependencies { name id }',
        formatter=DependencyListFormatter(),
    ),
])

session_fields_v5 = FieldSet([
    CliFieldSpec(
        'containers',
        subfields=FieldSet([
            CliFieldSpec('id', "Kernel ID", alt_name='kernel_id'),
            CliFieldSpec('session_id', "Session ID"),
            CliFieldSpec('role'),
            CliFieldSpec('agent'),
            CliFieldSpec('image'),
            CliFieldSpec('status'),
            CliFieldSpec('status_info'),
            CliFieldSpec('status_data', formatter=nested_dict_formatter),
            CliFieldSpec('status_changed'),
            CliFieldSpec('occupied_slots', formatter=resource_slot_formatter),
            CliFieldSpec('live_stat', formatter=KernelStatFormatter()),
            CliFieldSpec('last_stat', formatter=KernelStatFormatter()),
        ]),
        formatter=ContainerListFormatter(),
    ),
])


storage_fields = FieldSet([
    CliFieldSpec('id'),
    CliFieldSpec('backend'),
    CliFieldSpec('fsprefix'),
    CliFieldSpec('path'),
    CliFieldSpec('capabilities'),
    CliFieldSpec('hardware_metadata', formatter=nested_dict_formatter),
    CliFieldSpec('performance_metric', formatter=nested_dict_formatter),
    CliFieldSpec('usage', formatter=nested_dict_formatter),
])


user_fields = FieldSet([
    CliFieldSpec('uuid'),
    CliFieldSpec('username'),
    CliFieldSpec('email'),
    # password is not queriable!
    CliFieldSpec('need_password_change'),
    CliFieldSpec('full_name'),
    CliFieldSpec('description'),
    CliFieldSpec('is_active'),
    CliFieldSpec('status'),
    CliFieldSpec('status_info'),
    CliFieldSpec('created_at'),
    CliFieldSpec('modified_at'),
    CliFieldSpec('domain_name'),
    CliFieldSpec('role'),
    CliFieldSpec('groups { id name }', formatter=GroupListFormatter()),
])


vfolder_fields = FieldSet([
    CliFieldSpec('id'),
    CliFieldSpec('host'),
    CliFieldSpec('name'),
    CliFieldSpec('user', alt_name='user_id'),
    CliFieldSpec('group', alt_name='group_id'),
    CliFieldSpec('creator'),
    CliFieldSpec('unmanaged_path'),
    CliFieldSpec('usage_mode'),
    CliFieldSpec('permission'),
    CliFieldSpec('ownership_type'),
    CliFieldSpec('max_files'),
    CliFieldSpec('max_size'),
    CliFieldSpec('created_at'),
    CliFieldSpec('last_used'),
    CliFieldSpec('num_files'),
    CliFieldSpec('cur_size'),
    CliFieldSpec('cloneable'),
])
