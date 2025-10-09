import pytest

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


@pytest.fixture(scope="session")
def powershell() -> PowershellRunspace:
    return PowershellRunspace()
