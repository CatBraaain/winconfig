import re
from itertools import groupby
from typing import Self, cast

import httpx
from casing import pascalize
from pydantic import BaseModel, RootModel

from winconfig.model.definition.definition import (
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
    def pull(cls, definition_block: str) -> Self:
        definition_lines = definition_block.splitlines()
        calling = definition_lines[-1].removeprefix("# ").strip()
        name = cls.resolve_name(calling)
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

    @staticmethod
    def resolve_name(calling_line: str) -> str:
        elements = calling_line.split(" ")
        match len(elements):
            case 1:
                function_name = elements[0]
                param_name = ""
                has_arg = False
                name_src = function_name
            case 2:
                function_name = elements[0]
                param_name = elements[1]
                has_arg = False
                name_src = param_name + " " + function_name
            case _:
                function_name = elements[0]
                param_name = elements[1]
                has_arg = not elements[2].startswith("-")
                name_src = (
                    function_name if has_arg else param_name + " " + function_name
                )

        return pascalize(name_src)


class SophiaDefinition(RootModel):
    root: list[SophiaTaskDefinition] = []

    @classmethod
    def pull(cls) -> Self:
        definition_url = "https://raw.githubusercontent.com/farag2/Sophia-Script-for-Windows/refs/heads/master/src/Sophia_Script_for_Windows_11/Sophia.ps1"
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
            SophiaTaskDefinition.pull(td_source) for td_source in td_sources
        ]

        tds = [
            td
            for td in tds
            if td.id
            in [
                "FolderGroupBy",
                "SecondsInSystemClock",
                "ClockInNotificationCenter",
                "WindowsColorMode",
                "AppColorMode",
                "ShortcutsSuffix",
                "RestorePreviousFolders",
                "EditWithClipchampContext",
                "EditWithPhotosContext",
                "EditWithPaintContext",
                "PrintCMDContext",
                "CompressedFolderNewContext",
                "MultipleInvokeContext",
                "UseStoreOpenWith",
                "OpenWindowsTerminalContext",
                "OpenWindowsTerminalAdminContext",
            ]
        ]

        sophia_module_url = "https://raw.githubusercontent.com/farag2/Sophia-Script-for-Windows/refs/heads/master/src/Sophia_Script_for_Windows_11/Module/Sophia.psm1"
        sophia_module = httpx.get(sophia_module_url).text

        for td in tds:
            td.calling = (
                cast(
                    re.Match,
                    re.search(
                        rf"^function {td.function_name}.*?^[}}]",
                        sophia_module,
                        flags=re.MULTILINE | re.DOTALL,
                    ),
                ).group()
                + "\n"
                + td.calling
            )
        return cls(tds)

    def convert(self) -> Definition:
        target_tds = [
            td
            for td in self.root
            if not re.search(r"using \w+ pop-up", td.description)
            and td.function_name
            not in [
                # gui
                "Set-Association",
                "Export-Associations",
                "Import-Associations",
                "ScanRegistryPolicies",
                "Set-UserShellFolderLocation",
                "UnpinTaskbarShortcuts",
                # deps
                "DiagTrackService",
                "NetworkAdaptersSavePower",
                "ScheduledTasks",
                "Cursors",
                "OneDrive",
                "CleanupTask",
                "SoftwareDistributionTask",
                "TempTask",
                # other
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
            preload=None,
        )
