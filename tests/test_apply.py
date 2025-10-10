import pytest

from winconfig.model.definition import Definition
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator


def test_apply_resitory(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for registry in definition.registries:
        res = powershell.run(
            ScriptGenerator.generate_set_registry_script(registry, revert=revert)
        )
        if res == "<AccessDenied>":
            # pytest.skip("Access denied: need workaround")
            continue

        current_value = powershell.run(
            ScriptGenerator.generate_get_registry_script(registry)
        )
        expected_value = registry.resolve_value(revert)
        assert str(current_value) == str(expected_value), (
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
        assert current_state == "<NotExist>" or current_state == expected_value, (
            f"[{schtask.path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_apply_service(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for service in definition.services:
        res = powershell.run(
            ScriptGenerator.generate_set_service_script(service, revert=revert)
        )
        if res == "<AccessDenied>":
            # pytest.skip("Access denied: need workaround")
            continue
        if res == "<NotSupported>":
            # pytest.skip("Not supported: try with PowerShell 7")
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

        assert current_type == "<NotExist>" or current_type == expected_type, (
            f"[{service.name}]'s type '{current_type}' != '{expected_type}'"
        )


def test_apply_script(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    if definition.name == "Hiber":
        pytest.skip("Windows Sandbox not supporting Hibernation")

    script = ScriptGenerator.generate_script_script(definition.script, revert=revert)
    print(script)
    powershell.run(script)
