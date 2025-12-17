from enum import Enum
from typing import Literal, Self

from pydantic import RootModel


class ActionMode(Enum):
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
type ActionConfigRoot = dict[ActionGroupName, dict[ActionName, ActionMode]]


class ActionConfig(RootModel):
    root: ActionConfigRoot = {}

    @classmethod
    def merge(cls, action_configs: list[Self]) -> Self:
        merged: ActionConfigRoot = {}
        for action_config in action_configs:
            for group_name, group in action_config.root.items():
                if group_name not in merged:
                    merged[group_name] = {}
                merged[group_name] |= group

        return cls.model_validate(merged)
