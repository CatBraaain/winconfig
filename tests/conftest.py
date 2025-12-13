import pytest

from winconfig.dsl.action import ActionMode, ExecutableActionMode
from winconfig.dsl.definition import Definition
from winconfig.engine.model_loader import ModelLoader
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
    config = ModelLoader.load_config([])
    runspace = PowershellRunspace()
    runtime_sets = [
        (runspace, definition)
        for group in config.definition_config.groups
        for definition in group.definitions
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
    params=[ActionMode.APPLY, ActionMode.REVERT],
    ids=lambda e: e.value,
)
def mode(request: pytest.FixtureRequest) -> ExecutableActionMode:
    return request.param
