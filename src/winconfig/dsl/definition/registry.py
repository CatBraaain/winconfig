import re
from textwrap import dedent
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from winconfig.dsl.task_plan import ApplyMode, TaskMode

from .const_types import (
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


class RegistryBaseDefinition(BaseModel):
    path: str = Field(description="The path to the registry key.")

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


class RegistryEntryDefinition(RegistryBaseDefinition):
    """Represents a single registry entry value to be modified."""

    name: str = Field(description="The name of the registry value.")
    type: RegistryValueKind = Field(description="The type of the registry value.")
    old_value: str | NotExistType = Field(
        description="The default value of the registry entry."
    )
    new_value: str | NotExistType = Field(
        description="The desired value of the registry entry."
    )

    @property
    def full_path(self) -> str:
        return f"{self.path}\\{self.name}"

    def resolve_value(self, mode: ApplyMode) -> str:
        match mode:
            case TaskMode.APPLY:
                return self.new_value
            case TaskMode.REVERT:
                return self.old_value
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_set_script(self, mode: TaskMode) -> str:
        if mode == TaskMode.SKIP:
            return ""
        value = self.resolve_value(mode)
        if self.type == "Binary":
            psvalue = f'("{value.replace('"', '`"')}".split(" ") | % {{ [byte]$_ }})'
        else:
            psvalue = f'"{value.replace('"', '`"')}"'

        set_entry = rf"""
            if (!(Test-Path "{self.registry_path}")) {{
                New-Item -Path "{self.registry_path.replace("``*", "*")}" -Force -ErrorAction Stop | Out-Null
            }}
            try {{
                Set-ItemProperty -Path "{self.registry_path}" -Name "{self.name}" -Type "{self.type}" -Value {psvalue} -Force -ErrorAction Stop | Out-Null
            }}
            catch [System.UnauthorizedAccessException] {{
                "{ACCESS_DENIED}"
            }}
            catch [System.Security.SecurityException] {{
                "{PERMISSION_DENIED}"
            }}
        """
        remove_entry = rf"""
            try {{
                Remove-ItemProperty -Path "{self.registry_path}" -Name "{self.name}" -Force -ErrorAction Stop | Out-Null
            }}
            catch [System.Management.Automation.ItemNotFoundException] {{
                "{NOT_EXIST}"
            }}
            catch [System.Management.Automation.PSArgumentException] {{
                "{NOT_EXIST}"
            }}
            catch [System.Security.SecurityException] {{
                "{PERMISSION_DENIED}"
            }}
        """
        script = set_entry if value != NOT_EXIST else remove_entry

        return dedent(script)

    def generate_get_script(self) -> str:
        get_entry = rf"""
            try {{
                Get-ItemPropertyValue -Path "{self.registry_path}" -Name "{self.name}" -ErrorAction Stop
            }}
            catch [System.Management.Automation.ItemNotFoundException] {{
                "{NOT_EXIST}"
            }}
            catch [System.Management.Automation.PSArgumentException] {{
                "{NOT_EXIST}"
            }}
        """
        return dedent(get_entry)


class RegistryKeyDefinition(RegistryBaseDefinition):
    """Represents a single registry key to be modified."""

    old_value: NotChangeType | ExistType | NotExistType = Field(
        description="The default value of the registry entry."
    )
    new_value: NotChangeType | ExistType | NotExistType = Field(
        description="The desired value of the registry entry."
    )

    @property
    def full_path(self) -> str:
        return f"{self.registry_path}"

    def resolve_value(
        self, mode: ApplyMode
    ) -> NotChangeType | ExistType | NotExistType:
        match mode:
            case TaskMode.APPLY:
                return self.new_value
            case TaskMode.REVERT:
                return self.old_value
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_set_script(self, mode: TaskMode) -> str:
        if mode == TaskMode.SKIP:
            return ""
        value = self.resolve_value(mode)

        add_key = rf"""
            if (!(Test-Path "{self.registry_path}")) {{
                New-Item -Path "{self.registry_path}" -Force -ErrorAction Stop | Out-Null
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
