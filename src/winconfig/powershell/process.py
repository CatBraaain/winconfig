import clr
from pydantic import BaseModel, RootModel

dll_path = r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Management.Automation\v4.0_3.0.0.0__31bf3856ad364e35\System.Management.Automation.dll"
clr.AddReference(dll_path)  # pyright: ignore[reportAttributeAccessIssue]
from Microsoft.PowerShell import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    ExecutionPolicy,
)
from System.Management.Automation import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    PowerShell,
    Runspaces,
)


class FunctionDefinition(BaseModel):
    name: str
    script_block: str


class FunctionDefinitions(RootModel):
    root: list[FunctionDefinition]


class PowershellRunspace:
    runspace: Runspaces.Runspace
    version: int

    def __init__(self, preload: str | None = None) -> None:
        iss = Runspaces.InitialSessionState.CreateDefault()
        if preload:
            function_defs = self.extract_functions(preload)
            for function_def in function_defs.root:
                iss.Commands.Add(
                    Runspaces.SessionStateFunctionEntry(
                        function_def.name, function_def.script_block
                    )
                )
        iss.ExecutionPolicy = ExecutionPolicy.Bypass
        self.runspace = Runspaces.RunspaceFactory.CreateRunspace(iss)
        self.runspace.Open()
        self.version = self.runspace.Version.Major

    @classmethod
    def extract_functions(cls, preload: str) -> FunctionDefinitions:
        script = f"""
            $oldCommandNames = Get-Command | % {{ $_.Name }}
            $funcDef = @'{"\n" + preload + "\n"}'@
            iex $funcDef
            $commands = Get-Command
            $newCommands = @($commands | ? {{ $oldCommandNames -notcontains $_.Name }})
            ConvertTo-Json @($newCommands | % {{ @{{name = $_.Name; script_block = $_.ScriptBlock.ToString() }} }})
        """
        function_definitions_json = cls().run(script)
        return FunctionDefinitions.model_validate_json(function_definitions_json)

    def run(self, script: str) -> str:
        process = PowerShell.Create()
        process.Runspace = self.runspace
        process.AddScript(script, True)

        try:
            stdouts = process.Invoke()
            output = "\n".join(map(str, stdouts)).strip()

            if process.Streams.Error.Count > 0:
                stderrs = "\n".join(map(str, process.Streams.Error)).strip()
                raise Exception(stderrs)

            return output
        finally:
            process.Dispose()
