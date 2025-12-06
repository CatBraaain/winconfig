import pytest

from winconfig.dsl.const_types import ACCESS_DENIED, NOT_EXIST
from winconfig.dsl.definition import TaskDefinition, TaskMode
from winconfig.engine.powershell import PowershellRunspace


def test_apply_resitory(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], mode: TaskMode
):
    powershell, task_definition = runtime_set
    for registry in task_definition.registries:
        res = powershell.run(registry.generate_set_script(mode))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue

        current_value = powershell.run(registry.generate_get_script())
        if mode == TaskMode.SKIP:
            continue
        expected_value = registry.resolve_value(mode)
        assert current_value == expected_value, (
            f"[{registry.full_path}]'s value '{current_value}' != '{expected_value}'"
        )


def test_apply_scheduled_task(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], mode: TaskMode
):
    powershell, task_definition = runtime_set
    for schtask in task_definition.scheduled_tasks:
        powershell.run(schtask.generate_set_script(mode))
        current_state = powershell.run(schtask.generate_get_script())
        if mode == TaskMode.SKIP:
            continue
        expected_value = schtask.resolve_value(mode)
        assert current_state in (NOT_EXIST, expected_value), (
            f"[{schtask.full_path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_apply_service(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], mode: TaskMode
):
    powershell, task_definition = runtime_set
    for service in task_definition.services:
        res = powershell.run(service.generate_set_script(mode))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue
        current_type = powershell.run(service.generate_get_script())
        if mode == TaskMode.SKIP:
            continue
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


def test_apply_script(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], mode: TaskMode
):
    powershell, task_definition = runtime_set
    if task_definition.name in [
        "RemoveCopilot",
    ]:
        pytest.xfail("Not Supporting in Windows Sandbox")

    script = task_definition.script.generate_set_script(mode)
    powershell.run(script)
