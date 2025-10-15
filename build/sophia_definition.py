import re
from itertools import groupby
from typing import Self

import httpx
from casing import pascalize
from pydantic import BaseModel

from winconfig.model.definition import (
    Definition,
    ScriptDefinition,
    TaskDefinition,
)


class SophiaTaskDefinition(BaseModel):
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


class SophiaDefinition(BaseModel):
    task_definitions: list[SophiaTaskDefinition] = []
    preload: str | None = None

    @classmethod
    def from_remote(cls, definition_url: str, preload_script_urls: list[str]) -> Self:
        res = httpx.get(definition_url)
        sophia_script_block = re.sub(
            r".*#endregion Protection", "", res.text, flags=re.DOTALL
        ).strip()
        td_sources = re.split(
            r"^\n(?=^\S.*\n)", sophia_script_block, flags=re.MULTILINE
        )
        td_sources = [
            re.sub(r"^#(end)?region.*|<#|#>", "", block, flags=re.MULTILINE).strip()
            for block in td_sources
        ]
        tds: list[SophiaTaskDefinition] = [
            SophiaTaskDefinition.from_definition(td_source) for td_source in td_sources
        ]

        preload = "\n".join([httpx.get(url).text for url in preload_script_urls])
        return cls(
            task_definitions=tds,
            preload=preload or None,
        )

    def for_winconfig(self) -> Definition:
        target_tds = [
            td
            for td in self.task_definitions
            if not re.search(r"using \w+ pop-up", td.description)
            and td.function_name
            not in [
                "Set-Association",
                "Export-Associations",
                "Import-Associations",
                "ScanRegistryPolicies",
                "PostActions",
                "Errors",
            ]
        ]
        td_groups = [
            list(group)
            for key, group in groupby(target_tds, key=lambda d: d.function_name)
        ]

        tds = []
        for td_group in td_groups:
            td = next(td for td in td_group if not td.is_default)
            apply = td.calling
            revert = (
                next(td.calling for td in td_group if td.is_default)
                if len(td_group) > 1
                else None
            )
            tds.append(
                TaskDefinition(
                    id=td.id,
                    name=td.name,
                    description=td.description,
                    script=ScriptDefinition(apply=apply, revert=revert),
                )
            )

        return Definition(
            task_definitions=tds,
            preload=self.preload,
        )
