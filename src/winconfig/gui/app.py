from pathlib import Path
from typing import Any

from loguru import logger
from textual.app import App, ComposeResult
from textual.containers import Center
from textual.reactive import reactive
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
    running: reactive[bool] = reactive(default=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.engine = Engine()
        self.engine.config.merge_from_yaml(Path("samples/winconfig.config.yaml"))

    def compose(self) -> ComposeResult:
        yield Header()
        yield Body()
        yield Footer()

    def watch_running(self, _: bool, new_value: bool) -> None:  # noqa: FBT001
        is_running = new_value is True
        body = self.query_one(Body)
        if is_running:
            body.mount_log()
        else:
            body.mount_task_list()


class Body(Center):
    def compose(self) -> ComposeResult:
        yield RunButton()
        yield TaskList()

    def mount_task_list(self) -> None:
        self.remove_children()
        self.mount(
            RunButton(),
            TaskList(),
        )

    def mount_log(self) -> None:
        self.remove_children()
        self.mount(
            BackButton(),
            LogList(),
        )


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


class LogList(Log):
    BORDER_TITLE = "LogList"

    def on_mount(self) -> None:
        logger.configure(
            handlers=[
                {
                    "sink": self.write,
                    "format": "<green>{time:HH:mm:ss.SSS}</green> | <level>{message}</level>",
                    "level": "INFO",
                }
            ]  # ty:ignore[invalid-argument-type]  # loguru not having runtime type
        )


app = WinconfigApp()
