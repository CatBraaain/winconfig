import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    PlainSerializer,
    field_validator,
)

from winconfig.powershell.constants import NotExistType

type RegistryValueKind = Literal[
    "String",
    "ExpandString",
    "Binary",
    "DWord",
    "MultiString",
    "QWord",
]


class RegistryDefinition(BaseModel):
    """Represents a single registry value to be modified."""

    path: Annotated[
        str,
        PlainSerializer(lambda x: x.replace("Registry::", "")),
        Field(description="The path to the registry key."),
    ]
    name: str = Field(description="The name of the registry value.")
    type: RegistryValueKind = Field(description="The type of the registry value.")
    old_value: str | NotExistType = Field(
        description="The default value of the registry entry."
    )
    new_value: str | NotExistType = Field(
        description="The desired value of the registry entry."
    )

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
                "^(Registry::)?" + pattern,
                "Registry::" + repl,
                value,
                flags=re.IGNORECASE,
            )
        return value

    @property
    def full_path(self) -> str:
        return f"{self.path.replace('Registry::', '')}\\{self.name}"

    def resolve_value(self, revert: bool) -> str:
        return self.new_value if not revert else self.old_value
