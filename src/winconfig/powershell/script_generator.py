from textwrap import dedent

from winconfig.model.definition import (
    Definition,
    Registry,
    ScheduledTask,
    Script,
    Service,
)


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
        value = registry.new_value if not revert else registry.old_value

        ensure_key = rf"""
            If (!(Test-Path "{registry.path}")) {{
                New-Item -Path "{registry.path}" -Force -ErrorAction Stop | Out-Null
            }}
        """
        set_entry = rf"""
            Set-ItemProperty -Path "{registry.path}" -Name {registry.name} -Type {registry.type} -Value {registry.new_value} -Force -ErrorAction SilentlyContinue | Out-Null
        """
        remove_entry = rf"""
            Remove-ItemProperty -Path "{registry.path}" -Name {registry.name} -Force -ErrorAction SilentlyContinue | Out-Null
        """
        script = ensure_key + (set_entry if value != "<NotExist>" else remove_entry)

        return dedent(script)

    @staticmethod
    def generate_get_registry_script(registry: Registry) -> str:
        get_entry = rf"""
            try {{
                Get-ItemPropertyValue -Path "{registry.path}" -Name {registry.name} -ErrorAction Stop
            }}
            catch [System.Management.Automation.ItemNotFoundException] {{
                "<NotExist>"
            }}
            catch [System.Management.Automation.PSArgumentException] {{
                "<NotExist>"
            }}
        """
        return dedent(get_entry)

    @staticmethod
    def generate_set_schtask_script(schtask: ScheduledTask, revert: bool) -> str:
        state = schtask.new_state if not revert else schtask.old_state
        enable_task = f"""
            Enable-ScheduledTask -TaskName "{schtask.path}" -ErrorAction SilentlyContinue
        """
        disable_task = f"""
            Disable-ScheduledTask -TaskName "{schtask.path}" -ErrorAction SilentlyContinue
        """
        script = enable_task if state == "Enabled" else disable_task
        return dedent(script)

    @staticmethod
    def generate_get_schtask_script(schtask: ScheduledTask) -> str:
        get_task = f"""
            $taskState = Get-ScheduledTask | ? {{$_.TaskPath + $_.TaskName -eq "\\" + "{schtask.path}"}} | % {{$_.State}}
            $taskState = if ($taskState) {{ $taskState }} else {{ "<NotExist>" }}
            $taskState
        """
        return dedent(get_task)

    @staticmethod
    def generate_set_service_script(service: Service, revert: bool) -> str:
        startup_type = (
            service.new_startup_type if not revert else service.old_startup_type
        )
        script = f"""
            Set-Service -Name "{service.name}" -StartupType {startup_type} -ErrorAction SilentlyContinue
        """
        return dedent(script)

    @staticmethod
    def generate_get_service_script(service: Service) -> str:
        script = f"""
            try {{
                (Get-Service -Name "{service.name}" -ErrorAction Stop).StartType
            }}
            catch [Microsoft.PowerShell.Commands.ServiceCommandException] {{
                "<NotExist>"
            }}
        """
        return dedent(script)

    @staticmethod
    def generate_script_script(input_script: Script, revert: bool) -> str:
        script = (input_script.apply if not revert else input_script.revert) or ""
        return dedent(script)
