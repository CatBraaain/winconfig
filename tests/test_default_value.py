import pytest

from winconfig.model.definition import Definition
from winconfig.powershell.constants import NOT_EXIST
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator


@pytest.fixture(autouse=True)
def skip_this_test():
    pytest.skip("under consideration")


# pytestmark = pytest.mark.xfail(
#     strict=False, reason="under consideration"
# )


def test_default_resitory(powershell: PowershellRunspace, definition: Definition):
    for registry in definition.registries:
        script = ScriptGenerator.generate_get_registry_script(registry)
        current_value = powershell.run(script)
        expected_value = registry.old_value
        assert str(current_value) == str(expected_value), (
            f"[{registry.full_path}]'s value '{current_value}' != '{expected_value}'"
        )


def test_default_scheduled_task(powershell: PowershellRunspace, definition: Definition):
    for task in definition.scheduled_tasks:
        script = ScriptGenerator.generate_get_schtask_script(task)
        current_state = powershell.run(script)
        expected_state = task.old_state
        assert current_state in (NOT_EXIST, expected_state), (
            f"[{task.path}]'s state '{current_state}' != '{expected_state}'"
        )


def test_default_service(powershell: PowershellRunspace, definition: Definition):
    for service in definition.services:
        script = ScriptGenerator.generate_get_service_script(service)
        current_type = powershell.run(script)
        expected_type = service.old_startup_type
        assert current_type in (NOT_EXIST, expected_type), (
            f"[{service.name}]'s type '{current_type}' != '{expected_type}'"
        )
