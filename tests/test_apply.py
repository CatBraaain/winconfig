import pytest

from winconfig.model.definition import Definition
from winconfig.powershell.constants import ACCESS_DENIED, NOT_EXIST
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator


def test_apply_resitory(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for registry in definition.registries:
        res = powershell.run(
            ScriptGenerator.generate_set_registry_script(registry, revert=revert)
        )
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue

        current_value = powershell.run(
            ScriptGenerator.generate_get_registry_script(registry)
        )
        expected_value = registry.resolve_value(revert)
        assert current_value == expected_value, (
            f"[{registry.full_path}]'s value '{current_value}' != '{expected_value}'"
        )


def test_apply_scheduled_task(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for schtask in definition.scheduled_tasks:
        powershell.run(
            ScriptGenerator.generate_set_schtask_script(schtask, revert=revert)
        )
        current_state = powershell.run(
            ScriptGenerator.generate_get_schtask_script(schtask)
        )
        expected_value = schtask.resolve_value(revert)
        assert current_state in (NOT_EXIST, expected_value), (
            f"[{schtask.full_path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_apply_service(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for service in definition.services:
        res = powershell.run(
            ScriptGenerator.generate_set_service_script(service, revert=revert)
        )
        if res == ACCESS_DENIED:
            # pytest.skip("Access denied: need workaround")
            continue
        current_type = powershell.run(
            ScriptGenerator.generate_get_service_script(service)
        )
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
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    if definition.name in ["DisableHibernation", "DisableTelemetry", "RemoveOneDrive"]:
        pytest.skip("Windows Sandbox not supporting")

    if definition.name in [
        "ChangeWindowsTerminalDefault",
        "AdobeDebloat",
        "DisableMicrosoftCopilot",
    ]:
        pytest.skip("Not supported yet")

    if definition.name in [
        "DisableExplorerAutomaticFolderDiscovery",
        "DisableStorageSense",
        "BlockRazerSoftwareInstalls",
    ]:
        pytest.xfail("Need error handling")

    if definition.name in ["RunDiskCleanup", "CreateRestorePoint"]:
        pytest.skip("Save time")

    script = ScriptGenerator.generate_script_script(definition.script, revert=revert)
    powershell.run(script)
