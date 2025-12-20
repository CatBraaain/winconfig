from enum import StrEnum
from typing import Literal, Self

from pydantic import ConfigDict, RootModel


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

    model_config = ConfigDict(validate_assignment=True)

    def merge(self, action_configs: list[Self]) -> None:
        new_root: dict[ActionGroupName, dict[ActionName, ActionMode]] = self.root.copy()
        for action_config in action_configs:
            for group_name, group in action_config.root.items():
                if group_name not in new_root:
                    new_root[group_name] = {}
                new_root[group_name] |= group

        self.root = new_root
