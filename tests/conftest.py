from pathlib import Path

import pytest
import yaml

from winconfig.model.definition import DefinitionContainer
from winconfig.powershell.process import PowershellRunspace

DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil_definition.yaml")
definitions = DefinitionContainer.model_validate(
    yaml.safe_load(DEFINITIONS_FILE.read_text())
).root


@pytest.fixture(params=definitions, ids=[d.name for d in definitions])
def definition(request: pytest.FixtureRequest):
    return request.param


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


@pytest.fixture(scope="session")
def powershell() -> PowershellRunspace:
    return PowershellRunspace()


@pytest.fixture(
    params=[False, True],
    ids=["[apply]", "[revert]"],
)
def revert(request: pytest.FixtureRequest):
    return request.param
