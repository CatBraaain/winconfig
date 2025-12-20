import pytest

from winconfig.config.action import ActionMode, ExecutableActionMode
from winconfig.engine import Engine, Task
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


def generate_runtime_sets() -> list[tuple[PowershellRunspace, Task]]:
    engine = Engine()
    runspace = PowershellRunspace()
    runtime_sets = [(runspace, task) for group in engine.groups for task in group.tasks]
    return runtime_sets


@pytest.fixture(
    scope="session",
    params=generate_runtime_sets(),
    ids=lambda runtime_set: runtime_set[1].name,
)
def runtime_set(
    request: pytest.FixtureRequest,
) -> tuple[PowershellRunspace, Task]:
    return request.param


@pytest.fixture(
    params=[ActionMode.APPLY, ActionMode.REVERT],
    ids=lambda e: e,
)
def mode(request: pytest.FixtureRequest) -> ExecutableActionMode:
    return request.param
