import clr
import pytest

dll_path = r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Management.Automation\v4.0_3.0.0.0__31bf3856ad364e35\System.Management.Automation.dll"
clr.AddReference(dll_path)  # pyright: ignore[reportAttributeAccessIssue]
from Microsoft.PowerShell import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    ExecutionPolicy,
)
from System.Management.Automation import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    PowerShell,
    Runspaces,
)


class PowershellProcess:
    process: PowerShell

    def __init__(self, runspace: Runspaces.Runspace) -> None:
        self.process = PowerShell.Create()
        self.process.Runspace = runspace

    def run(self, script: str) -> str:
        self.process.Commands.AddScript(script, True)
        results = self.process.Invoke()
        self.process.Commands.Clear()  # perf: remove added scripts
        return "\n".join(map(str, results)).strip()


class PowershellRunspace:
    @staticmethod
    def create_runspace() -> Runspaces.Runspace:
        iss = Runspaces.InitialSessionState.CreateDefault()
        iss.ExecutionPolicy = ExecutionPolicy.Bypass
        runspace = Runspaces.RunspaceFactory.CreateRunspace(iss)
        runspace.Open()
        return runspace


@pytest.fixture(scope="session")
def powershell() -> PowershellProcess:
    return PowershellProcess(PowershellRunspace.create_runspace())
