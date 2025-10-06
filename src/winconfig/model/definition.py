from typing import Literal

from pydantic import BaseModel, ConfigDict, RootModel

from .config import ConfigElement
from .task import Task

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

    def generate_script(self, revert: bool) -> str:
        value = self.new_value if not revert else self.old_value
        # script = (
        #     f"reg add {self.path} /v {self.name} /t {self.type} /d {self.new_value} /f"
        #     if value is not None
        #     else f"reg delete {self.path} /v {self.name} /f"
        # )
        script = (
            f'If (!(Test-Path "{self.path}")) {{'
            f'    New-Item -Path "{self.path}" -Force -ErrorAction Stop | Out-Null'
            f"}}"
        ) + (
            f'Set-ItemProperty -Path "{self.path}" -Name {self.name} -Type {self.type} -Value {self.new_value} -Force -ErrorAction SilentlyContinue | Out-Null'
            if value != "<RemoveEntry>"
            else f'Remove-ItemProperty -Path "{self.path}" -Name {self.name} -Force -ErrorAction SilentlyContinue | Out-Null'
        )
        return script


type ScheduledTaskState = Literal["Enabled", "Disabled"]


class ScheduledTask(BaseModel):
    path: str
    old_state: ScheduledTaskState
    new_state: ScheduledTaskState

    def generate_script(self, revert: bool) -> str:
        state = self.new_state if not revert else self.old_state
        # script = (
        #     f"sc config {self.path} start= {self.new_state}"
        #     if state == "Enabled"
        #     else f"sc config {self.path} start= {self.new_state}"
        # )
        script = (
            f'Enable-ScheduledTask -TaskName "{self.path}" -ErrorAction SilentlyContinue'
            if state == "Enabled"
            else f'Disable-ScheduledTask -TaskName "{self.path}" -ErrorAction SilentlyContinue'
        )
        return script


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

    def generate_script(self, revert: bool) -> str:
        startup_type = self.new_startup_type if not revert else self.old_startup_type
        # script = f"sc config {self.name} start= {state}"
        script = f'Set-Service -Name "{self.name}" -StartupType {startup_type} -ErrorAction SilentlyContinue'
        return script


class Script(BaseModel):
    apply: str | None
    revert: str | None

    def generate_script(self, revert: bool) -> str:
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

    def generate_task(self, revert: bool) -> Task:
        script = "\n".join(
            [
                e.generate_script(revert)
                for e in (
                    self.registries
                    + self.scheduled_tasks
                    + self.services
                    + [self.script]
                )
            ]
        )
        return Task(
            name=self.name,
            revert=revert,
            script_code=script,
        )


class Definitions(RootModel):
    root: list[Definition] = []

    def generate_tasks(self, config_elements: list[ConfigElement]) -> list[Task]:
        return [
            self.get_definition(config_element.name).generate_task(
                config_element.revert
            )
            for config_element in config_elements
        ]

    def get_definition(self, task_name: str) -> Definition:
        definition = next((x for x in self.root if x.name == task_name), None)
        if definition is None:
            raise ValueError(f"Definition {task_name} not found")
        return definition
