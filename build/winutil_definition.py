import re
from typing import Literal

from pydantic import BaseModel, RootModel

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


class WinutilScheduledTask(BaseModel):
    Name: str
    OriginalState: Literal["Enabled", "Disabled"]
    State: Literal["Enabled", "Disabled"]


class WinutilService(BaseModel):
    Name: str
    OriginalType: ServiceStartupType
    StartupType: ServiceStartupType


class WinutilDefinition(BaseModel):
    Content: str
    Description: str = ""
    registry: list[WinutilRegistry] = []
    ScheduledTask: list[WinutilScheduledTask] = []
    service: list[WinutilService] = []
    InvokeScript: list[str] | None = None
    UndoScript: list[str] | None = None


class WinutilDefinitionContainer(RootModel):
    root: dict[str, WinutilDefinition]

    def to_definitions(self) -> DefinitionContainer:
        return DefinitionContainer(
            definitions=[
                Definition(
                    name=re.sub(r"WPFToggle|WPFTweaks", "", name),
                    description=winutil_def.Description,
                    registries=[
                        Registry(
                            path=registry.Path,
                            name=registry.Name,
                            type=registry.Type,
                            old_value=registry.OriginalValue.replace(
                                "<RemoveEntry>", NOT_EXIST
                            ),
                            new_value=registry.Value.replace(
                                "<RemoveEntry>", NOT_EXIST
                            ),
                        )
                        for registry in winutil_def.registry
                    ],
                    scheduled_tasks=[
                        ScheduledTask(
                            path=scheduled_task.Name,
                            old_state=scheduled_task.OriginalState,
                            new_state=scheduled_task.State,
                        )
                        for scheduled_task in winutil_def.ScheduledTask
                    ],
                    services=[
                        Service(
                            name=service.Name,
                            old_startup_type=service.OriginalType,
                            new_startup_type=service.StartupType,
                        )
                        for service in winutil_def.service
                    ],
                    script=Script(
                        apply="\n".join(winutil_def.InvokeScript or []).rstrip()
                        or None,
                        revert="\n".join(winutil_def.UndoScript or []).rstrip() or None,
                    ),
                )
                for name, winutil_def in self.root.items()
                if winutil_def.Description != ""
            ]
        )
