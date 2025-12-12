from enum import Enum
from typing import Literal

from pydantic import BaseModel, RootModel


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


type ApplyMode = Literal[ActionMode.APPLY, ActionMode.REVERT]

type ActionGroupName = str
type ActionGroup = dict[ActionName, ActionMode]
type ActionName = str
type ActionCollectionRoot = dict[ActionGroupName, ActionGroup]


class ActionCollection(RootModel):
    root: ActionCollectionRoot = {}
