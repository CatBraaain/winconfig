import subprocess
from pathlib import Path

import pytest
import yaml

from winconfig.generator.script_generator import ScriptGenerator
from winconfig.model.definition import Definition, DefinitionContainer

pytestmark = pytest.mark.xfail(
    strict=False, reason="Maybe someday, maybe never - under consideration"
)


DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil_definitions.yaml")
definitions = DefinitionContainer.model_validate(
    yaml.safe_load(DEFINITIONS_FILE.read_text())
).root


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_resitory(definition: Definition):
    for registry in definition.registries:
        script = ScriptGenerator.generate_get_registry_script(registry)
        result = run_powershell_command(script)

        current_value = result.stdout.strip()
        if registry.type == "REG_DWORD":
            current_value = str(int(current_value))

        assert str(current_value) == str(registry.old_value), (
            f"[{shorten(f'{registry.path}\\{registry.name}')}]'s value '{current_value}' != '{registry.old_value}'"
        )


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_scheduled_task(definition: Definition):
    for task in definition.scheduled_tasks:
        script = ScriptGenerator.generate_get_schtask_script(task)
        result = run_powershell_command(script)

        current_state = result.stdout.strip()
        assert current_state == "<NotExist>" or current_state == task.old_state, (
            f"[{task.path}]'s state '{current_state}' != '{task.old_state}'"
        )


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_service(definition: Definition):
    for service in definition.services:
        script = ScriptGenerator.generate_get_service_script(service)
        result = run_powershell_command(script)

        current_type = result.stdout.strip()
        assert (
            current_type == "<NotExist>" or current_type == service.old_startup_type
        ), f"[{service.name}]'s type '{current_type}' != '{service.old_startup_type}'"


def run_powershell_command(command: str):
    result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        check=True,
        text=True,
    )
    return result


def shorten(s: str, width: int = 50, placeholder: str = "...") -> str:
    s = s.replace("Registry::", "")
    return s if len(s) <= width else s[: width - len(placeholder)] + placeholder
