import re
from typing import Any, Literal, Self

import httpx
import yaml
from casing import camelize, pascalize
from pydantic import BaseModel, ConfigDict, RootModel

from winconfig.model.definition.definition import (
    Definition,
    RegistryDefinition,
    RegistryValueKind,
    SchtaskDefinition,
    ScriptDefinition,
    ServiceDefinition,
    ServiceStartupType,
    TaskDefinition,
)
from winconfig.powershell.constants import NOT_EXIST


class WinutilRegistryDefinition(BaseModel):
    Path: str
    Name: str
    Type: RegistryValueKind
    OriginalValue: str
    Value: str

    def convert(self) -> RegistryDefinition:
        return RegistryDefinition(
            path=self.Path,
            name=self.Name,
            type=self.Type,
            old_value=self.OriginalValue.replace("<RemoveEntry>", NOT_EXIST),
            new_value=self.Value.replace("<RemoveEntry>", NOT_EXIST),
        )


class WinutilScheduledTaskDefinition(BaseModel):
    Name: str
    OriginalState: Literal["Enabled", "Disabled"]
    State: Literal["Enabled", "Disabled"]

    def convert(self) -> SchtaskDefinition:
        return SchtaskDefinition(
            full_path=self.Name,
            old_state=self.OriginalState,
            new_state=self.State,
        )


class WinutilServiceDefinition(BaseModel):
    Name: str
    OriginalType: ServiceStartupType
    StartupType: ServiceStartupType

    def convert(self) -> ServiceDefinition:
        return ServiceDefinition(
            name=self.Name,
            old_startup=self.OriginalType,
            new_startup=self.StartupType,
        )


class WinutilTaskDefinition(BaseModel):
    id: str
    Content: str
    Description: str = ""
    Registry: list[WinutilRegistryDefinition] = []
    ScheduledTask: list[WinutilScheduledTaskDefinition] = []
    Service: list[WinutilServiceDefinition] = []
    InvokeScript: list[str] | None = None
    UndoScript: list[str] | None = None

    Type: Any | None = None
    Order: Any | None = None
    Panel: Any | None = None
    Category: Any | None = None
    Link: Any | None = None
    ButtonWidth: Any | None = None
    Appx: Any | None = None
    Checked: Any | None = None
    ComboItems: Any | None = None

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=lambda field_name: camelize(field_name),
        populate_by_name=True,
    )

    def convert(self) -> TaskDefinition:
        return TaskDefinition(
            id=re.sub(r"WPFToggle|WPFTweaks", "", self.id),
            name=pascalize(re.sub(r"( [^\s\w]|[^\s\w] ).*", "", self.Content)),
            description=self.Description,
            registries=[registry.convert() for registry in self.Registry],
            scheduled_tasks=[
                scheduled_task.convert() for scheduled_task in self.ScheduledTask
            ],
            services=[service.convert() for service in self.Service],
            script=ScriptDefinition(
                apply=self.resolve_script(self.InvokeScript),
                revert=self.resolve_script(self.UndoScript),
            ),
        )

    def resolve_script(self, value: list[str] | None) -> str | None:
        script = "\n".join(value or []).rstrip()
        script = re.sub(
            "Invoke-WinUtilExplorerUpdate.*(;|$)", "", script, flags=re.MULTILINE
        )
        script = re.sub(r"if \(\$sync.*\) \{[\s\S]*?\}", "", script)
        return script.strip() or None


class WinutilDefinition(RootModel):
    root: list[WinutilTaskDefinition]

    @classmethod
    def pull(cls) -> Self:
        definition_url = "https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/config/tweaks.json"
        res = httpx.get(definition_url)
        invalid_json = res.text
        fixed_json = re.sub(
            r"(\"(?:InvokeScript|UndoScript)\": \[\n\s*[\"'])([\s\S]*?)([\"']\n\s*],?\n)",
            lambda x: x.group(1)
            + re.sub(r"(\n\r? {0,6})", r"\\n", x.group(2).lstrip())
            + x.group(3),
            invalid_json,
        )
        return cls(
            [
                WinutilTaskDefinition.model_validate({"id": key, **value})
                for key, value in yaml.safe_load(fixed_json).items()
            ],
        )

    def convert(self) -> Definition:
        target_tds = [td for td in self.root if td.Description != ""]
        return Definition(
            task_definitions=[td.convert() for td in target_tds],
            preload=None,
        )
