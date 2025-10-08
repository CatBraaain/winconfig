from textwrap import dedent
from typing import Literal

from pydantic import BaseModel, ConfigDict, RootModel

# Why use PowerShell instead of reg.exe, sc.exe, or schtasks.exe?
# ---------------------------------------------------------------
# Tools like reg.exe, sc.exe, and schtasks.exe are effective for setting values
# but not for retrieving them in a structured format.
# PowerShell, on the other hand, allows reading and modifying system configuration
# objects (e.g., registry entries, services, scheduled tasks) as native objects.
# This makes it easier to verify that the expected values were applied correctly
# during automated testing.

type RegistryValueKind = Literal[
    "String",
    "ExpandString",
    "Binary",
    "DWord",
    "MultiString",
    "QWord",
]


class Registry(BaseModel):
    path: str
    name: str
    type: RegistryValueKind
    old_value: str | Literal["<RemoveEntry>"]  # noqa: PYI051
    new_value: str | Literal["<RemoveEntry>"]  # noqa: PYI051

    def generate_execution_script(self, revert: bool) -> str:
        value = self.new_value if not revert else self.old_value

        ensure_key = rf"""\
            If (!(Test-Path "{self.path}")) {{
                New-Item -Path "{self.path}" -Force -ErrorAction Stop | Out-Null
            }}
        """
        set_entry = rf"""\
            Set-ItemProperty -Path "{self.path}" -Name {self.name} -Type {self.type} -Value {self.new_value} -Force -ErrorAction SilentlyContinue | Out-Null
        """
        remove_entry = rf"""\
            Remove-ItemProperty -Path "{self.path}" -Name {self.name} -Force -ErrorAction SilentlyContinue | Out-Null
        """
        script = ensure_key + (set_entry if value != "<RemoveEntry>" else remove_entry)
        return dedent(script)


type ScheduledTaskState = Literal["Enabled", "Disabled"]


class ScheduledTask(BaseModel):
    path: str
    old_state: ScheduledTaskState
    new_state: ScheduledTaskState

    def generate_execution_script(self, revert: bool) -> str:
        state = self.new_state if not revert else self.old_state
        enable_task = f"""
            Enable-ScheduledTask -TaskName "{self.path}" -ErrorAction SilentlyContinue
        """
        disable_task = f"""
            Disable-ScheduledTask -TaskName "{self.path}" -ErrorAction SilentlyContinue
        """
        script = enable_task if state == "Enabled" else disable_task
        return dedent(script)


type ServiceStartupType = Literal[
    "Automatic",
    "AutomaticDelayedStart",
    "Disabled",
    "InvalidValue",
    "Manual",
]


class Service(BaseModel):
    name: str
    old_startup_type: ServiceStartupType
    new_startup_type: ServiceStartupType

    def generate_execution_script(self, revert: bool) -> str:
        startup_type = self.new_startup_type if not revert else self.old_startup_type
        script = f"""
            Set-Service -Name "{self.name}" -StartupType {startup_type} -ErrorAction SilentlyContinue
        """
        return dedent(script)


class Script(BaseModel):
    apply: str | None
    revert: str | None

    def generate_execution_script(self, revert: bool) -> str:
        script = (self.apply if not revert else self.revert) or ""
        return script


class Definition(BaseModel):
    name: str
    description: str
    registries: list[Registry] = []
    scheduled_tasks: list[ScheduledTask] = []
    services: list[Service] = []
    script: Script = Script(apply=None, revert=None)

    model_config = ConfigDict(
        # use_enum_values=False,
        extra="forbid",
        json_schema_extra={
            "anyOf": [
                {"required": ["registries"]},
                {"required": ["scheduled_tasks"]},
                {"required": ["services"]},
                {"required": ["script"]},
            ]
        },
    )

    def generate_execution_script(self, revert: bool) -> str:
        return "\n".join(
            [
                e.generate_execution_script(revert)
                for e in (
                    self.registries
                    + self.scheduled_tasks
                    + self.services
                    + [self.script]
                )
            ]
        )


class DefinitionContainer(RootModel):
    root: list[Definition] = []

    def get_definition(self, task_name: str) -> Definition:
        definition = next((x for x in self.root if x.name == task_name), None)
        if definition is None:
            raise ValueError(f"Definition {task_name} not found")
        return definition
