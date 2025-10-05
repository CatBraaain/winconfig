from pydantic import BaseModel


class Task(BaseModel):
    name: str
    revert: bool
    script_code: str
