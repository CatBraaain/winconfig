import pytest

from winconfig.model.definition.definition import TaskDefinition
from winconfig.powershell.constants import NOT_EXIST
from winconfig.powershell.process import PowershellRunspace
from winconfig.powershell.script_generator import ScriptGenerator


@pytest.fixture(autouse=True)
def skip_this_test():
    pytest.skip("under consideration")


# pytestmark = pytest.mark.xfail(
#     strict=False, reason="under consideration"
# )


def test_default_resitory(runtime_set: tuple[PowershellRunspace, TaskDefinition]):
    powershell, task_definition = runtime_set
    for registry in task_definition.registries:
        script = ScriptGenerator.registry_get(registry)
        current_value = powershell.run(script)
        expected_value = registry.old_value
        assert current_value in (NOT_EXIST, expected_value), (
            f"[{registry.full_path}]'s value '{current_value}' != '{expected_value}'"
        )


def test_default_scheduled_task(runtime_set: tuple[PowershellRunspace, TaskDefinition]):
    powershell, task_definition = runtime_set
    for task in task_definition.scheduled_tasks:
        script = ScriptGenerator.schtask_get(task)
        current_state = powershell.run(script)
        expected_state = task.old_state
        assert current_state in (NOT_EXIST, expected_state), (
            f"[{task.full_path}]'s state '{current_state}' != '{expected_state}'"
        )


def test_default_service(runtime_set: tuple[PowershellRunspace, TaskDefinition]):
    powershell, task_definition = runtime_set
    for service in task_definition.services:
        script = ScriptGenerator.service_get(service)
        current_type = powershell.run(script)
        expected_type = service.old_startup
        assert current_type in (NOT_EXIST, expected_type), (
            f"[{service.name}]'s type '{current_type}' != '{expected_type}'"
        )
