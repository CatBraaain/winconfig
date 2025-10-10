import pytest

from winconfig.model.definition import Definition
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator

pytestmark = pytest.mark.xfail(
    strict=False, reason="Maybe someday, maybe never - under consideration"
)


def test_default_resitory(powershell: PowershellRunspace, definition: Definition):
    for registry in definition.registries:
        script = ScriptGenerator.generate_get_registry_script(registry)
        current_value = powershell.run(script)

        assert str(current_value) == str(registry.old_value), (
            f"[{registry.path.replace('Registry::', '')}\\{registry.name}]'s value '{current_value}' != '{registry.old_value}'"
        )


def test_default_scheduled_task(powershell: PowershellRunspace, definition: Definition):
    for task in definition.scheduled_tasks:
        script = ScriptGenerator.generate_get_schtask_script(task)
        current_state = powershell.run(script)

        assert current_state == "<NotExist>" or current_state == task.old_state, (
            f"[{task.path}]'s state '{current_state}' != '{task.old_state}'"
        )


def test_default_service(powershell: PowershellRunspace, definition: Definition):
    for service in definition.services:
        script = ScriptGenerator.generate_get_service_script(service)
        current_type = powershell.run(script)

        assert (
            current_type == "<NotExist>" or current_type == service.old_startup_type
        ), f"[{service.name}]'s type '{current_type}' != '{service.old_startup_type}'"
