from textwrap import dedent, indent
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from winconfig.dsl.action import ActionMode, ExecutableActionMode

from .const_types import NOT_EXIST

type ServiceStartupType = Literal[
    "Automatic",
    "AutomaticDelayedStart",
    "Disabled",
    "InvalidValue",
    "Manual",
]


class ServiceDefinition(BaseModel):
    """Represents a Windows service to be modified."""

    name: str = Field(description="The name of the service.")
    old_startup: ServiceStartupType = Field(
        description="The default startup type of the service."
    )
    new_startup: ServiceStartupType = Field(
        description="The desired startup type of the service."
    )

    model_config = ConfigDict(extra="forbid")

    def resolve_value(self, mode: ExecutableActionMode) -> str:
        match mode:
            case ActionMode.APPLY:
                return self.new_startup
            case ActionMode.REVERT:
                return self.old_startup
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def with_error_handler(self, script: str) -> str:
        return f"""
            try {{
                {indent(dedent(script), " " * 4).lstrip()}
            }}
            catch [System.Management.Automation.ParameterBindingException] {{
                throw
            }}
            catch [System.InvalidOperationException] {{
                "{NOT_EXIST}"
            }}
            catch [Microsoft.PowerShell.Commands.ServiceCommandException] {{
                "{NOT_EXIST}"
            }}
        """

    def generate_set_script(self, mode: ExecutableActionMode) -> str:
        startup_type = self.resolve_value(mode)

        service_name = f"""
            $serviceName = "{self.name}"
        """
        service_name_by_glob = f"""
            $service = @(Get-Service -Name "{self.name}" -ErrorAction Stop)[0]
            if ($service -eq $null) {{ "{NOT_EXIST}"; return }}
            $serviceName = $service.Name
        """
        body = self.with_error_handler(f"""
            Set-Service -Name "$serviceName" -StartupType "{startup_type.replace("DelayedStart", "")}" -ErrorAction Stop | Out-Null
        """)
        script = (service_name if "*" not in self.name else service_name_by_glob) + body
        return dedent(script)

    def generate_get_script(self) -> str:
        script = self.with_error_handler(f"""
            $startupType = (Get-Service -Name "{self.name}" -ErrorAction Stop).StartType
            $isDelayed = (Get-ItemProperty "Registry::HKLM\\SYSTEM\\CurrentControlSet\\Services\\{self.name}").DelayedAutostart
            if ($startupType -eq "Automatic" -and $isDelayed -eq 1) {{ $startupType = "AutomaticDelayedStart" }}
            if ($startupType -eq $null) {{ $startupType = "{NOT_EXIST}" }}
            $startupType
        """)
        return dedent(script)
