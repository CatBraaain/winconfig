import pytest

from winconfig.dsl.action import ExecutableActionMode
from winconfig.dsl.definition import (
    ACCESS_DENIED,
    NOT_EXIST,
)
from winconfig.engine.config_context import Task
from winconfig.engine.powershell import PowershellRunspace


def test_resitory_definition(
    runtime_set: tuple[PowershellRunspace, Task], mode: ExecutableActionMode
):
    powershell, task = runtime_set
    for registry_path in task.registries:
        for registry_item in registry_path.items:
            res = powershell.run(registry_item.generate_set_script(mode))
            if res == ACCESS_DENIED:
                # pytest.skip("Access denied: need workaround")
                continue

            current_value = powershell.run(registry_item.generate_get_script())
            expected_value = registry_item.resolve_value(mode)
            assert current_value == expected_value, (
                f"[{registry_item.full_path}]'s value '{current_value}' != '{expected_value}'"
            )


def test_schtask_definiton(
    runtime_set: tuple[PowershellRunspace, Task], mode: ExecutableActionMode
):
    powershell, task = runtime_set
    for schtask in task.scheduled_tasks:
        powershell.run(schtask.generate_set_script(mode))
        current_state = powershell.run(schtask.generate_get_script())
        expected_value = schtask.resolve_value(mode)
        assert current_state in (NOT_EXIST, expected_value), (
            f"[{schtask.full_path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_service_definition(
    runtime_set: tuple[PowershellRunspace, Task], mode: ExecutableActionMode
):
    powershell, task = runtime_set
    for service in task.services:
        res = powershell.run(service.generate_set_script(mode))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue
        current_type = powershell.run(service.generate_get_script())
        expected_type = service.resolve_value(mode)
        if powershell.version == 5 and (
            current_type == "AutomaticDelayedStart"
            or expected_type == "AutomaticDelayedStart"
        ):
            # pytest.skip("Not supported: try with PowerShell 7")
            continue

        assert current_type in (NOT_EXIST, expected_type), (
            f"[{service.name}]'s type '{current_type}' != '{expected_type}'"
        )


def test_script_definition(
    runtime_set: tuple[PowershellRunspace, Task], mode: ExecutableActionMode
):
    powershell, task = runtime_set
    if task.name in [
        "RemoveCopilot",
    ]:
        pytest.xfail("Windows Sandbox does not support winget")

    script = task.script.generate_set_script(mode)
    powershell.run(script)
