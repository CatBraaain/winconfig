from winconfig.model.definition import Definition
from winconfig.model.task import Task
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator


def test_apply_resitory(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for registry in definition.registries:
        powershell.run(
            ScriptGenerator.generate_set_registry_script(registry, revert=revert)
        )
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
        assert current_state == expected_value, (
            f"[{schtask.path}]'s state '{current_state}' != '{expected_value}'"
        )


def test_apply_service(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    for service in definition.services:
        powershell.run(
            ScriptGenerator.generate_set_service_script(service, revert=revert)
        )
        current_type = powershell.run(
            ScriptGenerator.generate_get_service_script(service)
        )
        expected_type = service.resolve_value(revert)
        assert current_type == expected_type, (
            f"[{service.name}]'s type '{current_type}' != '{expected_type}'"
        )


def test_apply_all(
    powershell: PowershellRunspace, definition: Definition, revert: bool
):
    task = Task.from_definition(definition=definition, revert=revert)
    powershell.run(task.execution_script)
