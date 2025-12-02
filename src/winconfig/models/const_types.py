from typing import Final, Literal

type ApplyMode = Literal["apply", "revert"]

ACCESS_DENIED: Final = "<AccessDenied>"
NOT_EXIST = "<NotExist>"
type NotExistType = Literal["<NotExist>"]
EXIST = "<Exist>"
type ExistType = Literal["<Exist>"]
NOT_CHANGE = "<NotChange>"
type NotChangeType = Literal["<NotChange>"]
