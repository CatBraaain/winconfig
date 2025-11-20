from textwrap import dedent

from winconfig.model.definition.definition import (
    RegistryDefinition,
    SchtaskDefinition,
    ScriptDefinition,
    ServiceDefinition,
    TaskDefinition,
)
from winconfig.powershell.constants import ACCESS_DENIED, NOT_EXIST


class ScriptGenerator:
    @classmethod
    def generate_execution(cls, task_definition: TaskDefinition, revert: bool) -> str:
        return "\n".join(
            [
                cls.registry_set(registry, revert)
                for registry in task_definition.registries
            ]
            + [
                cls.schtask_set(task, revert)
                for task in task_definition.scheduled_tasks
            ]
            + [cls.service_set(service, revert) for service in task_definition.services]
            + [cls.custom_script(task_definition.script, revert)]
        )

    @staticmethod
    def registry_set(registry: RegistryDefinition, revert: bool) -> str:
        value = registry.resolve_value(revert)

        ensure_key = rf"""
            If (!(Test-Path "{registry.path}")) {{
                New-Item -Path "{registry.path}" -Force -ErrorAction Stop | Out-Null
            }}
        """
        set_entry = rf"""
            try {{
                Set-ItemProperty -Path "{registry.path}" -Name "{registry.name}" -Type "{registry.type}" -Value "{value}" -Force -ErrorAction Stop | Out-Null
            }}
            catch [System.UnauthorizedAccessException] {{
                "{ACCESS_DENIED}"
            }}
        """
        remove_entry = rf"""
            try {{
                Remove-ItemProperty -Path "{registry.path}" -Name "{registry.name}" -Force -ErrorAction Stop | Out-Null
            }}
            catch [System.Management.Automation.PSArgumentException] {{
                "{NOT_EXIST}"
            }}
        """
        script = ensure_key + (set_entry if value != NOT_EXIST else remove_entry)

        return dedent(script)

    @staticmethod
    def registry_get(registry: RegistryDefinition) -> str:
        get_entry = rf"""
            try {{
                Get-ItemPropertyValue -Path "{registry.path}" -Name "{registry.name}" -ErrorAction Stop
            }}
            catch [System.Management.Automation.ItemNotFoundException] {{
                "{NOT_EXIST}"
            }}
            catch [System.Management.Automation.PSArgumentException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(get_entry)

    @staticmethod
    def schtask_set(schtask: SchtaskDefinition, revert: bool) -> str:
        state = schtask.resolve_value(revert)
        enabled = "$true" if state == "Enabled" else "$false"
        script = f"""
            try {{
                $service = New-Object -ComObject "Schedule.Service"
                $service.Connect()
                $service.GetFolder("\").GetTask("{schtask.full_path}").Enabled = {enabled}
            }}
            catch [System.IO.FileNotFoundException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(script)

    @staticmethod
    def schtask_get(schtask: SchtaskDefinition) -> str:
        get_task = f"""
            try {{
                $service = New-Object -ComObject "Schedule.Service"
                $service.Connect()
                $enabled = $service.GetFolder("\").GetTask("{schtask.full_path}").Enabled
                $ret = if ($enabled) {{ "Enabled" }} else {{ "Disabled" }}
                $ret
            }}
            catch [System.IO.FileNotFoundException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(get_task)

    @staticmethod
    def service_set(service: ServiceDefinition, revert: bool) -> str:
        startup_type = service.resolve_value(revert)

        service_name = f"""
            $serviceName = "{service.name}"
        """
        service_name_by_glob = f"""
            $service = @(Get-Service -Name "{service.name}" -ErrorAction Stop)[0]
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
            service_name if "*" not in service.name else service_name_by_glob
        ) + body
        return dedent(script)

    @staticmethod
    def service_get(service: ServiceDefinition) -> str:
        script = f"""
            try {{
                $startupType = (Get-Service -Name "{service.name}" -ErrorAction Stop).StartType
                $isDelayed = (Get-ItemProperty "Registry::HKLM\\SYSTEM\\CurrentControlSet\\Services\\{service.name}").DelayedAutostart
                if ($startupType -eq "Automatic" -and $isDelayed -eq 1) {{ $startupType = "AutomaticDelayedStart" }}
                if ($startupType -eq $null) {{ $startupType = "{NOT_EXIST}" }}
                $startupType
            }}
            catch [Microsoft.PowerShell.Commands.ServiceCommandException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(script)

    @staticmethod
    def custom_script(input_script: ScriptDefinition, revert: bool) -> str:
        script = input_script.resolve_value(revert) or ""
        return dedent(script)
