import pytest

from winconfig.powershell.process import PowershellRunspace


@pytest.fixture(scope="session")
def powershell() -> PowershellRunspace:
    return PowershellRunspace()
