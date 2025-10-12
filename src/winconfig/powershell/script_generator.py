from textwrap import dedent

from winconfig.model.definition import (
    Definition,
    Registry,
    ScheduledTask,
    Script,
    Service,
)
from winconfig.powershell.constants import ACCESS_DENIED, NOT_EXIST


class ScriptGenerator:
    @classmethod
    def generate_script(cls, definition: Definition, revert: bool) -> str:
        return "\n".join(
            [
                cls.generate_set_registry_script(registry, revert)
                for registry in definition.registries
            ]
            + [
                cls.generate_set_schtask_script(task, revert)
                for task in definition.scheduled_tasks
            ]
            + [
                cls.generate_set_service_script(service, revert)
                for service in definition.services
            ]
            + [cls.generate_script_script(definition.script, revert)]
        )

    @staticmethod
    def generate_set_registry_script(registry: Registry, revert: bool) -> str:
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
    def generate_get_registry_script(registry: Registry) -> str:
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
    def generate_set_schtask_script(schtask: ScheduledTask, revert: bool) -> str:
        state = schtask.resolve_value(revert)
        enable_task = f"""
            try {{
                Enable-ScheduledTask -TaskName "{schtask.full_path}" -ErrorAction Stop | Out-Null
            }}
            catch [Microsoft.Management.Infrastructure.CimException] {{
                "{NOT_EXIST}"
            }}
        """
        disable_task = f"""
            try {{
                Disable-ScheduledTask -TaskName "{schtask.full_path}" -ErrorAction Stop | Out-Null
            }}
            catch [Microsoft.Management.Infrastructure.CimException] {{
                "{NOT_EXIST}"
            }}
        """
        script = enable_task if state == "Enabled" else disable_task
        return dedent(script)

    @staticmethod
    def generate_get_schtask_script(schtask: ScheduledTask) -> str:
        get_task = f"""
            try {{
                $taskState = (Get-ScheduledTask -TaskPath "{schtask.path}" -TaskName "{schtask.name}" -ErrorAction Stop).State
            }}
            catch [Microsoft.PowerShell.Cmdletization.Cim.CimJobException] {{
                "{NOT_EXIST}"; return
            }}
            if ($taskState -eq "Ready") {{ $taskState = "Enabled" }}
            $taskState
        """
        return dedent(get_task)

    @staticmethod
    def generate_set_service_script(service: Service, revert: bool) -> str:
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
    def generate_get_service_script(service: Service) -> str:
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
    def generate_script_script(input_script: Script, revert: bool) -> str:
        script = input_script.resolve_value(revert) or ""
        return dedent(script)
