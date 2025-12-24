from __future__ import annotations

import json
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import yaml
from textual.containers import HorizontalGroup
from textual.message import Message
from textual.widgets import Button, Log

from winconfig.engine import Engine

from .root_access_mixin import RootAccessMixin

if TYPE_CHECKING:
    from textual.app import ComposeResult


class TaskListController(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield RunButton()
        yield ImportButton()
        yield ExportButton()


class LogListController(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield BackButton()


class RunButton(Button, RootAccessMixin):
    def __init__(self) -> None:
        super().__init__(
            "Run",
            variant="primary",
            flat=True,
        )

    async def on_button_pressed(self, _: Button.Pressed) -> None:
        self.root.running = True
        try:
            self.root.engine.run(reverse=False)
        except Exception as e:  # noqa: BLE001
            self.app.screen.query_one(Log).write(str(e))


class ImportButton(Button, RootAccessMixin):
    def __init__(self) -> None:
        super().__init__(
            "Import",
            variant="primary",
            flat=True,
        )

    class Imported(Message):
        pass

    def on_button_pressed(self, _: Button.Pressed) -> None:
        result = subprocess.run(  # noqa: S603
            [
                "powershell",
                "-Command",
                dedent(
                    """
                    Add-Type -TypeDefinition @"
                        using System.Runtime.InteropServices;
                        public class DPIAware {
                            [DllImport("user32.dll")]
                            public static extern bool SetProcessDPIAware();
                        }
                    "@
                    [DPIAware]::SetProcessDPIAware() | Out-Null
                    Add-Type -AssemblyName System.Windows.Forms
                    $dialog = New-Object System.Windows.Forms.OpenFileDialog
                    $dialog.Filter = 'yaml files (*.yaml)|*.yaml|All files (*.*)|*.*'
                    @{
                        "success" = if ($dialog.ShowDialog() -eq "OK") { $true }else { $false }
                        "path"   = $dialog.FileName
                    } | ConvertTo-Json
                    """
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        ps_result = json.loads(result.stdout.strip())
        if ps_result["success"]:
            self.root.engine = Engine()
            self.root.engine.config.merge_from_yaml(Path(ps_result["path"]))
            self.post_message(self.Imported())


class ExportButton(Button, RootAccessMixin):
    def __init__(self) -> None:
        super().__init__(
            "Export",
            variant="primary",
            flat=True,
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        result = subprocess.run(  # noqa: S603
            [
                "powershell",
                "-Command",
                dedent(
                    """
                    Add-Type -TypeDefinition @"
                        using System.Runtime.InteropServices;
                        public class DPIAware {
                            [DllImport("user32.dll")]
                            public static extern bool SetProcessDPIAware();
                        }
                    "@
                    [DPIAware]::SetProcessDPIAware() | Out-Null
                    Add-Type -AssemblyName System.Windows.Forms
                    $dialog = New-Object System.Windows.Forms.SaveFileDialog
                    $dialog.Filter = 'yaml files (*.yaml)|*.yaml|All files (*.*)|*.*'
                    $dialog.FileName = 'winconfig.config.yaml'
                    @{
                        "success" = if ($dialog.ShowDialog() -eq "OK") { $true }else { $false }
                        "path"   = $dialog.FileName
                    } | ConvertTo-Json
                    """
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        ps_result = json.loads(result.stdout.strip())
        if ps_result["success"]:
            Path(ps_result["path"]).write_text(
                yaml.safe_dump(json.loads(self.root.engine.config.model_dump_json()))
            )


class BackButton(Button, RootAccessMixin):
    def __init__(self) -> None:
        super().__init__(
            "Back",
            variant="primary",
            flat=True,
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.root.running = False
