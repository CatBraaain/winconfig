import pytest

from winconfig.models.definition import TaskDefinition
from winconfig.powershell.constants import ACCESS_DENIED, NOT_EXIST
from winconfig.powershell.process import PowershellRunspace


def test_apply_resitory(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    for registry in task_definition.registries:
        res = powershell.run(registry.generate_set_script(revert=revert))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue

        current_value = powershell.run(registry.generate_get_script())
        expected_value = registry.resolve_value(revert)
        assert current_value == expected_value, (
            f"[{registry.full_path}]'s value '{current_value}' != '{expected_value}'"
        )


def test_apply_scheduled_task(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    for schtask in task_definition.scheduled_tasks:
        powershell.run(schtask.generate_set_script(revert=revert))
        current_state = powershell.run(schtask.generate_get_script())
        expected_value = schtask.resolve_value(revert)
        assert current_state in (NOT_EXIST, expected_value), (
            f"[{schtask.full_path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_apply_service(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    for service in task_definition.services:
        res = powershell.run(service.generate_set_script(revert=revert))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue
        current_type = powershell.run(service.generate_get_script())
        expected_type = service.resolve_value(revert)
        if powershell.version == 5 and (
            current_type == "AutomaticDelayedStart"
            or expected_type == "AutomaticDelayedStart"
        ):
            # pytest.skip("Not supported: try with PowerShell 7")
            continue

        assert current_type in (NOT_EXIST, expected_type), (
            f"[{service.name}]'s type '{current_type}' != '{expected_type}'"
        )


def test_apply_script(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    if task_definition.name in [
        "RemoveCopilot",
    ]:
        pytest.xfail("Windows Sandbox not supporting")

    script = task_definition.script.generate_custom_script(revert=revert)
    powershell.run(script)
