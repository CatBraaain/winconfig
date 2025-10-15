import re
from itertools import groupby
from typing import Self

import httpx
from casing import pascalize
from pydantic import BaseModel

from winconfig.model.definition import (
    Definition,
    DefinitionContainer,
    Script,
)


class SophiaDefinition(BaseModel):
    id: str
    name: str
    description: str
    function_name: str
    calling: str
    is_default: bool

    @classmethod
    def from_definition(cls, definition_block: str) -> Self:
        definition_lines = definition_block.splitlines()
        calling = definition_lines[-1].removeprefix("# ").strip()
        name = pascalize(" ".join(calling.split(" ")[::-1]))
        description = definition_lines[0].removeprefix("# ").strip()
        function_name = calling.split(" ")[0]
        is_default = (
            "(default value)" in description
            or "-Default" in calling
            or "-Delete" in calling
        )
        return cls(
            id=function_name,
            name=name,
            description=description,
            function_name=function_name,
            calling=calling,
            is_default=is_default,
        )


class SophiaDefinitionContainer(BaseModel):
    definitions: list[SophiaDefinition] = []
    preload: str

    @classmethod
    def from_url(cls, definition_url: str, preload_script_urls: list[str]) -> Self:
        res = httpx.get(definition_url)
        script_block = re.sub(
            r".*#endregion Protection", "", res.text, flags=re.DOTALL
        ).strip()
        definition_blocks = re.split(
            r"^\n(?=^\S.*\n)", script_block, flags=re.MULTILINE
        )
        definition_blocks = [
            re.sub(r"^#(end)?region.*|<#|#>", "", block, flags=re.MULTILINE).strip()
            for block in definition_blocks
        ]
        definitions: list[SophiaDefinition] = [
            SophiaDefinition.from_definition(definition_block)
            for definition_block in definition_blocks
        ]

        preload = "\n".join([httpx.get(url).text for url in preload_script_urls])
        return cls(
            definitions=definitions,
            preload=preload,
        )

    def to_winconfig_definition(self) -> DefinitionContainer:
        target_definitions = [
            definition
            for definition in self.definitions
            if not re.search(r"using \w+ pop-up", definition.description)
            and definition.calling
            not in [
                "Set-Association",
                "Export-Associations",
                "Import-Associations",
                "ScanRegistryPolicies",
                "PostActions",
                "Errors",
            ]
        ]
        definition_groups = [
            list(group)
            for key, group in groupby(target_definitions, key=lambda d: d.function_name)
        ]

        definitions = []
        for definition_group in definition_groups:
            definition = next(
                definition
                for definition in definition_group
                if not definition.is_default
            )
            apply = definition.calling
            revert = (
                next(
                    definition.calling
                    for definition in definition_group
                    if definition.is_default
                )
                if len(definition_group) > 1
                else None
            )
            definitions.append(
                Definition(
                    id=definition.id,
                    name=definition.name,
                    description=definition.description,
                    script=Script(apply=apply, revert=revert),
                )
            )

        return DefinitionContainer(
            definitions=definitions,
            preload=self.preload,
        )
