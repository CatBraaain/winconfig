import pytest

from winconfig.powershell.process import PowershellProcess, PowershellRunspace


@pytest.fixture(scope="session")
def powershell() -> PowershellProcess:
    return PowershellProcess(PowershellRunspace.create_runspace())
