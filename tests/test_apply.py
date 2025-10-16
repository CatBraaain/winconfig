import pytest

from winconfig.model.definition import TaskDefinition
from winconfig.powershell.constants import ACCESS_DENIED, NOT_EXIST
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator


def test_apply_resitory(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    for registry in task_definition.registries:
        res = powershell.run(ScriptGenerator.registry_set(registry, revert=revert))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue

        current_value = powershell.run(ScriptGenerator.registry_get(registry))
        expected_value = registry.resolve_value(revert)
        assert current_value == expected_value, (
            f"[{registry.full_path}]'s value '{current_value}' != '{expected_value}'"
        )


def test_apply_scheduled_task(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    for schtask in task_definition.scheduled_tasks:
        powershell.run(ScriptGenerator.schtask_set(schtask, revert=revert))
        current_state = powershell.run(ScriptGenerator.schtask_get(schtask))
        expected_value = schtask.resolve_value(revert)
        assert current_state in (NOT_EXIST, expected_value), (
            f"[{schtask.full_path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_apply_service(
    runtime_set: tuple[PowershellRunspace, TaskDefinition], revert: bool
):
    powershell, task_definition = runtime_set
    for service in task_definition.services:
        res = powershell.run(ScriptGenerator.service_set(service, revert=revert))
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue
        current_type = powershell.run(ScriptGenerator.service_get(service))
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
        # winutil
        "DisableHibernation",
        "DisableTelemetry",
        # sophia
        "EnableWindowsSandbox",
    ]:
        pytest.skip("Windows Sandbox not supporting")

    if task_definition.name in [
        # winutil
        "DisableExplorerAutomaticFolderDiscovery",
        "DisableStorageSense",
        "BlockRazerSoftwareInstalls",
        "AdobeDebloat",
        # sophia
        "WindowsTerminalDefaultTerminalApp",
        "NoneFolderGroupBy",
    ]:
        pytest.xfail("Need error handling")

    if task_definition.name in [
        # winutil
        "RunDiskCleanup",
        "CreateRestorePoint",
        "DisableMicrosoftCopilot",  # need winget
        "ChangeWindowsTerminalDefault",  # need winget
        "RemoveOneDrive",  # need winget
        # sophia
        "InstallDotNetRuntimes",
        "InstallVcRedist",
    ]:
        pytest.skip("Save time")

    script = ScriptGenerator.custom_script(task_definition.script, revert=revert)
    powershell.run(script)
    # System.Management.Automation.ItemNotFoundException
