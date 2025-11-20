from textwrap import dedent
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

from winconfig.powershell.constants import ACCESS_DENIED, NOT_EXIST

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

    def resolve_value(self, revert: bool) -> str:
        return self.new_startup if not revert else self.old_startup

    def generate_set_script(self, revert: bool) -> str:
        startup_type = self.resolve_value(revert)

        service_name = f"""
            $serviceName = "{self.name}"
        """
        service_name_by_glob = f"""
            $service = @(Get-Service -Name "{self.name}" -ErrorAction Stop)[0]
            if ($service -eq $null) {{ "{NOT_EXIST}"; return }}
            $serviceName = $service.Name
        """
        body = f"""
            try {{
                Set-Service -Name "$serviceName" -StartupType "{startup_type.replace("DelayedStart", "")}" -ErrorAction Stop | Out-Null
            }}
            catch [System.Management.Automation.ParameterBindingException] {{
                throw
            }}
            catch [System.InvalidOperationException] {{
                "{NOT_EXIST}"
            }}
            catch [Microsoft.PowerShell.Commands.ServiceCommandException] {{
                "{ACCESS_DENIED}"
            }}
        """
        script = (
            service_name if "*" not in self.name else service_name_by_glob
        ) + body
        return dedent(script)

    def generate_get_script(self) -> str:
        script = f"""
            try {{
                $startupType = (Get-Service -Name "{self.name}" -ErrorAction Stop).StartType
                $isDelayed = (Get-ItemProperty "Registry::HKLM\\SYSTEM\\CurrentControlSet\\Services\\{self.name}").DelayedAutostart
                if ($startupType -eq "Automatic" -and $isDelayed -eq 1) {{ $startupType = "AutomaticDelayedStart" }}
                if ($startupType -eq $null) {{ $startupType = "{NOT_EXIST}" }}
                $startupType
            }}
            catch [Microsoft.PowerShell.Commands.ServiceCommandException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(script)
