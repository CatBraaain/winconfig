from __future__ import annotations

import re
from textwrap import dedent, indent
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from winconfig.config.action import ActionMode, ExecutableActionMode
from winconfig.protocol.state_codes import (
    ACCESS_DENIED,
    EXIST,
    NOT_CHANGE,
    NOT_EXIST,
    PERMISSION_DENIED,
    ExistType,
    NotChangeType,
    NotExistType,
)

type RegistryValueKind = Literal[
    "String",
    "ExpandString",
    "Binary",
    "DWord",
    "MultiString",
    "QWord",
]


class RegistryPathDefinition(BaseModel):
    """Represents a single registry key and entry(s) to be modified."""

    path: str = Field(description="The path to the registry key.")
    old_existence: NotChangeType | ExistType | NotExistType = Field(
        default=EXIST,
        description="The default existance of the registry key.",
    )
    new_existence: NotChangeType | ExistType | NotExistType = Field(
        default=EXIST,
        description="The desired existance of the registry key.",
    )
    entries: list[RegistryEntryDefinition] = Field(
        default=[],
        description="The registry entries to be modified.",
    )

    model_config = ConfigDict(extra="forbid")

    def model_post_init(self, _: Any) -> None:  # noqa: ANN401
        for entry in self.entries:
            entry._parent = self  # noqa: SLF001

    @field_validator("path", mode="after")
    @staticmethod
    def normalize_path(value: str) -> str:
        mapping = {
            r"(HKEY_CLASSES_ROOT|HKCR):?\\": r"HKCR\\",
            r"(HKEY_CURRENT_CONFIG|HKCC):?\\": r"HKCC\\",
            r"(HKEY_CURRENT_USER|HKCU):?\\": r"HKCU\\",
            r"(HKEY_LOCAL_MACHINE|HKLM):?\\": r"HKLM\\",
            r"(HKEY_USERS|HKU):?\\": r"HKU\\",
        }

        for pattern, repl in mapping.items():
            value = re.sub(
                "^(?:Registry::)?" + pattern,
                repl,
                value,
                flags=re.IGNORECASE,
            )
        return value

    @property
    def registry_path(self) -> str:
        return f"Registry::{self.path.replace('*', '``*')}"

    @property
    def full_path(self) -> str:
        return f"{self.path}"

    @property
    def items(self) -> list[Self | RegistryEntryDefinition]:
        return [self, *self.entries]

    def resolve_value(
        self, mode: ExecutableActionMode
    ) -> NotChangeType | ExistType | NotExistType:
        match mode:
            case ActionMode.APPLY:
                return self.new_existence
            case ActionMode.REVERT:
                return self.old_existence
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_set_script(self, mode: ActionMode) -> str:
        if mode == ActionMode.SKIP:
            return ""
        value = self.resolve_value(mode)

        add_key = rf"""
            if (!(Test-Path "{self.registry_path}")) {{
                New-Item -Path "{self.registry_path.replace("``*", "*")}" -Force -ErrorAction Stop | Out-Null
            }}
        """
        remove_key = rf"""
            if (Test-Path "{self.registry_path}") {{
                Remove-Item -Path "{self.registry_path}" -Force -Recurse -ErrorAction Stop | Out-Null
            }}
        """
        if value == NOT_EXIST:
            script = remove_key
        elif value == EXIST:
            script = add_key
        elif value == NOT_CHANGE:
            script = ""
        else:
            raise ValueError(f"Invalid value: {value}")

        return dedent(script)

    def generate_get_script(self) -> str:
        get_entry = rf"""
            if (Test-Path "{self.registry_path}") {{
                "{EXIST}"
            }} else {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(get_entry)


class RegistryEntryDefinition(BaseModel):
    """Represents a single registry entry value to be modified."""

    name: str = Field(description="The name of the registry value.")
    type: RegistryValueKind = Field(description="The type of the registry value.")
    old_value: str | NotExistType = Field(
        description="The default value of the registry entry."
    )
    new_value: str | NotExistType = Field(
        description="The desired value of the registry entry."
    )

    _parent: RegistryPathDefinition = PrivateAttr(default=None)  # ty:ignore[invalid-assignment]

    model_config = ConfigDict(extra="forbid")

    @property
    def registry_path(self) -> str:
        return f"{self._parent.registry_path}"

    @property
    def full_path(self) -> str:
        return f"{self._parent.path}\\{self.name}"

    def resolve_value(self, mode: ExecutableActionMode) -> str:
        match mode:
            case ActionMode.APPLY:
                return self.new_value
            case ActionMode.REVERT:
                return self.old_value
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def with_error_handler(self, script: str) -> str:
        return f"""
            try {{
                {indent(dedent(script), " " * 4).lstrip()}
            }}
            catch [System.Management.Automation.ItemNotFoundException] {{
                "{NOT_EXIST}"
            }}
            catch [System.Management.Automation.PSArgumentException] {{
                "{NOT_EXIST}"
            }}
            catch [System.UnauthorizedAccessException] {{
                "{ACCESS_DENIED}"
            }}
            catch [System.Security.SecurityException] {{
                "{PERMISSION_DENIED}"
            }}
        """

    def generate_set_script(self, mode: ExecutableActionMode) -> str:
        value = self.resolve_value(mode)
        if self.type == "Binary":
            psvalue = f'("{value.replace('"', '`"')}".split(" ") | % {{ [byte]$_ }})'
        else:
            psvalue = f'"{value.replace('"', '`"')}"'

        set_entry = self.with_error_handler(rf"""
            Set-ItemProperty -Path "{self.registry_path}" -Name "{self.name}" -Type "{self.type}" -Value {psvalue} -Force -ErrorAction Stop | Out-Null
        """)
        remove_entry = self.with_error_handler(rf"""
            Remove-ItemProperty -Path "{self.registry_path}" -Name "{self.name}" -Force -ErrorAction Stop | Out-Null
        """)
        script = set_entry if value != NOT_EXIST else remove_entry

        return dedent(script)

    def generate_get_script(self) -> str:
        get_entry = self.with_error_handler(rf"""
            Get-ItemPropertyValue -Path "{self.registry_path}" -Name "{self.name}" -ErrorAction Stop
        """)
        return dedent(get_entry)
