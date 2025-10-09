from pathlib import Path

import pytest
import yaml

from winconfig.model.definition import Definition, DefinitionContainer
from winconfig.powershell.script_generator import ScriptGenerator

from .conftest import PowershellProcess

pytestmark = pytest.mark.xfail(
    strict=False, reason="Maybe someday, maybe never - under consideration"
)


DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil_definitions.yaml")
definitions = DefinitionContainer.model_validate(
    yaml.safe_load(DEFINITIONS_FILE.read_text())
).root


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_resitory(definition: Definition, powershell: PowershellProcess):
    for registry in definition.registries:
        script = ScriptGenerator.generate_get_registry_script(registry)
        current_value = powershell.run(script)

        assert str(current_value) == str(registry.old_value), (
            f"[{registry.path.replace('Registry::', '')}\\{registry.name}]'s value '{current_value}' != '{registry.old_value}'"
        )


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_scheduled_task(definition: Definition, powershell: PowershellProcess):
    for task in definition.scheduled_tasks:
        script = ScriptGenerator.generate_get_schtask_script(task)
        current_state = powershell.run(script)

        assert current_state == "<NotExist>" or current_state == task.old_state, (
            f"[{task.path}]'s state '{current_state}' != '{task.old_state}'"
        )


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_service(definition: Definition, powershell: PowershellProcess):
    for service in definition.services:
        script = ScriptGenerator.generate_get_service_script(service)
        current_type = powershell.run(script)

        assert (
            current_type == "<NotExist>" or current_type == service.old_startup_type
        ), f"[{service.name}]'s type '{current_type}' != '{service.old_startup_type}'"
