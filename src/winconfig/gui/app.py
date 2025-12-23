from pathlib import Path
from typing import Any

from loguru import logger
from textual.app import App, ComposeResult
from textual.containers import Center
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Log,
)

from winconfig.engine import Engine

from .root_access_mixin import RootAccessMixin
from .task_list import TaskList


class WinconfigApp(App):
    TITLE = "winconfig"
    CSS_PATH = "app.tcss"

    engine: Engine

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.engine = Engine()
        self.engine.config.merge_from_yaml(Path("samples/winconfig.config.yaml"))

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            yield RunButton()
            yield TaskList()
        yield Footer()


class LogScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Log()

    def on_mount(self) -> None:
        log = self.query_one(Log)
        logger.configure(
            handlers=[
                {
                    "sink": log.write,
                    "format": "<green>{time:HH:mm:ss.SSS}</green> | <level>{message}</level>",
                    "level": "INFO",
                }
            ]  # ty:ignore[invalid-argument-type]  # loguru not having runtime type
        )


class RunButton(Button, RootAccessMixin):
    def __init__(self) -> None:
        super().__init__(
            "Run",
            variant="primary",
            flat=True,
        )

    async def on_button_pressed(self, _: Button.Pressed) -> None:
        await self.app.push_screen(LogScreen())
        try:
            self.root.engine.run(reverse=False)
        except Exception as e:  # noqa: BLE001
            self.app.screen.query_one(Log).write(str(e))


app = WinconfigApp()
