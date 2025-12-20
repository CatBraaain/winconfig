from enum import StrEnum
from typing import Literal, Self

from pydantic import RootModel


class ActionMode(StrEnum):
    APPLY = "apply"
    REVERT = "revert"
    SKIP = "skip"

    def resolve(self, reverse: bool) -> "ActionMode":
        if reverse:
            if self == ActionMode.APPLY:
                return ActionMode.REVERT
            if self == ActionMode.REVERT:
                return ActionMode.APPLY
        return self


type ExecutableActionMode = Literal[ActionMode.APPLY, ActionMode.REVERT]

type ActionName = str
type ActionGroupName = str


class ActionConfig(RootModel):
    root: dict[ActionGroupName, dict[ActionName, ActionMode]] = {}

    def merge(self, action_configs: list[Self]) -> None:
        merged: dict[ActionGroupName, dict[ActionName, ActionMode]] = self.root.copy()
        for action_config in action_configs:
            for group_name, group in action_config.root.items():
                if group_name not in merged:
                    merged[group_name] = {}
                merged[group_name] |= group

        validated = self.model_validate(merged)
        self.root = validated.root
