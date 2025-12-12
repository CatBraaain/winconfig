from pathlib import Path

import pytest
import yaml

from winconfig.dsl.definition import ActionMode, Definition, DefinitionCollection
from winconfig.engine.powershell import PowershellRunspace


@pytest.fixture(autouse=True, scope="session")
def ensure_sandbox():
    is_sandbox = (
        PowershellRunspace().run(
            '((Get-WmiObject Win32_ComputerSystem).Model -eq "Virtual Machine")'
        )
        == "True"
    )
    if not is_sandbox:
        pytest.fail("This test must be run inside a Windows Sandbox")


def generate_runtime_sets() -> list[tuple[PowershellRunspace, Definition]]:
    definition_files = list(Path().glob("src/winconfig/resources/*.definition.yaml"))
    definitions = [
        DefinitionCollection.model_validate(
            yaml.safe_load(definition_file.read_text(encoding="utf-8"))
        )
        for definition_file in definition_files
    ]
    runspace_with_definition = [
        (PowershellRunspace(), definition) for definition in definitions
    ]
    runtime_sets = [
        (
            runspace,
            definition.get_definition(task_group_name, task_name),
        )
        for (runspace, definition) in runspace_with_definition
        for task_group_name, task_group in definition.root.items()
        for task_name in task_group
    ]
    return runtime_sets


@pytest.fixture(
    scope="session",
    params=generate_runtime_sets(),
    ids=lambda runtime_set: runtime_set[1].name,
)
def runtime_set(
    request: pytest.FixtureRequest,
) -> tuple[PowershellRunspace, Definition]:
    return request.param


@pytest.fixture(
    params=[ActionMode.APPLY, ActionMode.REVERT, ActionMode.SKIP],
    ids=lambda e: e.value,
)
def mode(request: pytest.FixtureRequest) -> ActionMode:
    return request.param
