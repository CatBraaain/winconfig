from pathlib import Path

import pytest
import yaml

from winconfig.model.definition import Definition
from winconfig.powershell.process import PowershellRunspace


@pytest.fixture(autouse=True, scope="session")
def ensure_sandbox(powershell: PowershellRunspace):
    is_sandbox = (
        powershell.run(
            '((Get-WmiObject Win32_ComputerSystem).Model -eq "Virtual Machine")'
        )
        == "True"
    )
    if not is_sandbox:
        pytest.fail("This test must be run inside a Windows Sandbox")


DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil.definition.yaml")
definition = Definition.model_validate(yaml.safe_load(DEFINITIONS_FILE.read_text()))
task_definitions = definition.task_definitions


@pytest.fixture(params=task_definitions, ids=[d.name for d in task_definitions])
def task_definition(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture(scope="session")
def powershell() -> PowershellRunspace:
    return PowershellRunspace(preload=definition.preload)


@pytest.fixture(
    params=[False, True],
    ids=["Apply", "Revert"],
)
def revert(request: pytest.FixtureRequest):
    return request.param
