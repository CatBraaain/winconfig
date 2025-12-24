from __future__ import annotations

import subprocess
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

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


class BackButton(Button, RootAccessMixin):
    def __init__(self) -> None:
        super().__init__(
            "Back",
            variant="primary",
            flat=True,
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.root.running = False


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
                    $dialog.ShowDialog() | Out-Null
                    $dialog.FileName
                    """
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        path = result.stdout.strip()

        self.root.engine = Engine()
        self.root.engine.config.merge_from_yaml(Path(path))
        self.post_message(self.Imported())
