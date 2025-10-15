import re
from typing import Any, Literal, Self

import httpx
import yaml
from casing import camelize, pascalize
from pydantic import BaseModel, ConfigDict

from winconfig.model.definition import (
    Definition,
    DefinitionContainer,
    Registry,
    RegistryValueKind,
    ScheduledTask,
    Script,
    Service,
    ServiceStartupType,
)
from winconfig.powershell.constants import NOT_EXIST


class WinutilRegistry(BaseModel):
    Path: str
    Name: str
    Type: RegistryValueKind
    OriginalValue: str
    Value: str

    def for_winconfig(self) -> Registry:
        return Registry(
            path=self.Path,
            name=self.Name,
            type=self.Type,
            old_value=self.OriginalValue.replace("<RemoveEntry>", NOT_EXIST),
            new_value=self.Value.replace("<RemoveEntry>", NOT_EXIST),
        )


class WinutilScheduledTask(BaseModel):
    Name: str
    OriginalState: Literal["Enabled", "Disabled"]
    State: Literal["Enabled", "Disabled"]

    def for_winconfig(self) -> ScheduledTask:
        return ScheduledTask(
            full_path=self.Name,
            old_state=self.OriginalState,
            new_state=self.State,
        )


class WinutilService(BaseModel):
    Name: str
    OriginalType: ServiceStartupType
    StartupType: ServiceStartupType

    def for_winconfig(self) -> Service:
        return Service(
            name=self.Name,
            old_startup_type=self.OriginalType,
            new_startup_type=self.StartupType,
        )


class WinutilDefinition(BaseModel):
    id: str
    Content: str
    Description: str = ""
    Registry: list[WinutilRegistry] = []
    ScheduledTask: list[WinutilScheduledTask] = []
    Service: list[WinutilService] = []
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

    def for_winconfig(self) -> Definition:
        return Definition(
            id=re.sub(r"WPFToggle|WPFTweaks", "", self.id),
            name=pascalize(re.sub(r"( [^\s\w]|[^\s\w] ).*", "", self.Content)),
            description=self.Description,
            registries=[registry.for_winconfig() for registry in self.Registry],
            scheduled_tasks=[
                scheduled_task.for_winconfig() for scheduled_task in self.ScheduledTask
            ],
            services=[service.for_winconfig() for service in self.Service],
            script=Script(
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


class WinutilDefinitionContainer(BaseModel):
    definitions: list[WinutilDefinition]
    preload: str | None = None

    @classmethod
    def from_winutil_url(
        cls, definition_url: str, preload_script_urls: list[str]
    ) -> Self:
        res = httpx.get(definition_url)
        invalid_json = res.text
        fixed_json = re.sub(
            r"(\"(?:InvokeScript|UndoScript)\": \[\n\s*[\"'])([\s\S]*?)([\"']\n\s*],?\n)",
            lambda x: x.group(1)
            + re.sub(r"(\n\r? {0,6})", r"\\n", x.group(2).lstrip())
            + x.group(3),
            invalid_json,
        )
        preload = "\n".join([httpx.get(url).text for url in preload_script_urls])
        return cls(
            definitions=[
                WinutilDefinition.model_validate({"id": key, **value})
                for key, value in yaml.safe_load(fixed_json).items()
            ],
            preload=preload,
        )

    def for_winconfig(self) -> DefinitionContainer:
        target_definitions = [
            winutil_def
            for winutil_def in self.definitions
            if winutil_def.Description != ""
        ]
        return DefinitionContainer(
            definitions=[
                winutil_def.for_winconfig() for winutil_def in target_definitions
            ],
            preload=self.preload,
        )
