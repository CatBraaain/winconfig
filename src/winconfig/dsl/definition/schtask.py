from pathlib import Path
from textwrap import dedent
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

from winconfig.dsl.task_plan import ApplyMode, TaskMode

from .const_types import NOT_EXIST

type SchtaskState = Literal["Enabled", "Disabled"]


class SchtaskDefinition(BaseModel):
    """Represents a scheduled task to be enabled or disabled."""

    full_path: str = Field(description="The full path of the scheduled task.")
    old_state: SchtaskState = Field(
        description="The default state of the scheduled task."
    )
    new_state: SchtaskState = Field(
        description="The desired state of the scheduled task."
    )

    @property
    def formatted_path(self) -> str:
        return "\\" + self.full_path.removeprefix("\\")

    @property
    def path(self) -> str:
        return str(Path(self.formatted_path).parent.as_posix()) + "/"

    @property
    def name(self) -> str:
        return Path(self.formatted_path).name

    def resolve_value(self, mode: ApplyMode) -> str:
        match mode:
            case TaskMode.APPLY:
                return self.new_state
            case TaskMode.REVERT:
                return self.old_state
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_set_script(self, mode: TaskMode) -> str:
        if mode == TaskMode.SKIP:
            return ""
        state = self.resolve_value(mode)
        enabled = "$true" if state == "Enabled" else "$false"
        script = f"""
            try {{
                $service = New-Object -ComObject "Schedule.Service"
                $service.Connect()
                $service.GetFolder("\\").GetTask("{self.full_path}").Enabled = {enabled}
            }}
            catch [System.IO.FileNotFoundException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(script)

    def generate_get_script(self) -> str:
        get_task = f"""
            try {{
                $service = New-Object -ComObject "Schedule.Service"
                $service.Connect()
                $enabled = $service.GetFolder("\\").GetTask("{self.full_path}").Enabled
                $ret = if ($enabled) {{ "Enabled" }} else {{ "Disabled" }}
                $ret
            }}
            catch [System.IO.FileNotFoundException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(get_task)
