import clr

dll_path = r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Management.Automation\v4.0_3.0.0.0__31bf3856ad364e35\System.Management.Automation.dll"
clr.AddReference(dll_path)  # ty:ignore[unresolved-attribute]
from Microsoft.PowerShell import (  # ty:ignore[unresolved-import]  # noqa: E402
    ExecutionPolicy,
)
from System.Management.Automation import (  # ty:ignore[unresolved-import] # noqa: E402
    PowerShell,
    Runspaces,
)


class PowershellRunspace:
    runspace: Runspaces.Runspace
    version: int

    def __init__(self) -> None:
        iss = Runspaces.InitialSessionState.CreateDefault()
        iss.ExecutionPolicy = ExecutionPolicy.Bypass
        self.runspace = Runspaces.RunspaceFactory.CreateRunspace(iss)
        self.runspace.Open()
        self.version = self.runspace.Version.Major

    def run(self, script: str) -> str:
        process = PowerShell.Create()
        process.Runspace = self.runspace
        process.AddScript(script, useLocalScope=True)

        try:
            stdouts = process.Invoke()
            if process.Streams.Error.Count > 0:
                stderrs = "\n".join(map(str, process.Streams.Error)).strip()
                raise Exception(stderrs)

            output = "\n".join(map(str, stdouts)).strip()
            return output
        finally:
            process.Dispose()
