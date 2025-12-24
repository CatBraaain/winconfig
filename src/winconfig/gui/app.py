from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Center
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
)

from winconfig.engine import Engine

from .content import LogList, TaskList
from .controller import LogListController, TaskListController


class WinconfigApp(App):
    TITLE = "winconfig"
    CSS_PATH = "app.tcss"

    engine: Engine
    running: reactive[bool] = reactive(default=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.engine = Engine()

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
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
        yield TaskListController()
        yield TaskList()

    def mount_task_list(self) -> None:
        self.remove_children()
        self.mount(
            TaskListController(),
            TaskList(),
        )

    def mount_log(self) -> None:
        self.remove_children()
        self.mount(
            LogListController(),
            LogList(),
        )

    def on_import_button_imported(self) -> None:
        self.mount_task_list()


app = WinconfigApp()
