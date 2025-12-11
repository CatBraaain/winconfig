from pathlib import Path

import pytest
import yaml

from winconfig.dsl.definition import Definition, TaskDefinition, TaskMode
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


def generate_runtime_sets() -> list[tuple[PowershellRunspace, TaskDefinition]]:
    definition_files = list(Path().glob("src/winconfig/resources/*.definition.yaml"))
    definitions = [
        Definition.model_validate(
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
            TaskDefinition.model_validate({"name": name, **td_body.model_dump()}),
        )
        for (runspace, definition) in runspace_with_definition
        for name, td_body in definition.root.items()
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
    params=[TaskMode.APPLY, TaskMode.REVERT, TaskMode.SKIP],
    ids=lambda e: e.value,
)
def mode(request: pytest.FixtureRequest) -> TaskMode:
    return request.param
