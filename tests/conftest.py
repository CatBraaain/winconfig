from pathlib import Path

import pytest
import yaml

from winconfig.model.definition.definition import Definition, TaskDefinition
from winconfig.powershell.process import PowershellRunspace


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


def generate_runtime_sets() -> list[tuple[PowershellRunspace, TaskDefinition]]:
    definition_files = list(Path().glob("src/winconfig/definitions/*.definition.yaml"))
    definitions = [
        Definition.model_validate(
            yaml.safe_load(definition_file.read_text(encoding="utf-8"))
        )
        for definition_file in definition_files
    ]
    runspace_with_definition = [
        (PowershellRunspace(preload=definition.preload), definition)
        for definition in definitions
    ]
    runtime_sets = [
        (runspace, task_definition)
        for (runspace, definition) in runspace_with_definition
        for task_definition in definition.task_definitions
    ]
    return runtime_sets


@pytest.fixture(
    scope="session",
    params=generate_runtime_sets(),
    ids=lambda runtime_set: runtime_set[1].name,
)
def runtime_set(
    request: pytest.FixtureRequest,
) -> tuple[PowershellRunspace, TaskDefinition]:
    return request.param


@pytest.fixture(
    params=[False, True],
    ids=["Apply", "Revert"],
)
def revert(request: pytest.FixtureRequest):
    return request.param
