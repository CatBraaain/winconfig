from enum import Enum
from typing import Final, Literal


class TaskMode(Enum):
    APPLY = "apply"
    REVERT = "revert"
    SKIP = "skip"


type ApplyMode = Literal[TaskMode.APPLY, TaskMode.REVERT]

ACCESS_DENIED: Final = "<AccessDenied>"
NOT_EXIST = "<NotExist>"
type NotExistType = Literal["<NotExist>"]
EXIST = "<Exist>"
type ExistType = Literal["<Exist>"]
NOT_CHANGE = "<NotChange>"
type NotChangeType = Literal["<NotChange>"]
