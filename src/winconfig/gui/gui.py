from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Container, Grid, Middle
from textual.events import Focus
from textual.widgets import (
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Select,
)

from winconfig.config.action import ActionMode
from winconfig.engine import Engine, Task


class WinconfigApp(App):
    TITLE = "winconfig"
    CSS_PATH = "gui.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            yield TaskList()
        yield Footer()


class TaskList(ListView):
    BORDER_TITLE = "TaskList"

    def __init__(self) -> None:
        engine = Engine(Path("samples/winconfig.config.yaml"))
        super().__init__(
            *[
                TaskListItem(task=task)
                for group in engine.task_groups
                for task in group.tasks
            ],
        )


class TaskListItem(ListItem):
    task_: Task

    def __init__(self, task: Task) -> None:
        super().__init__(classes=f"{task.group_name} {task.name}")
        self.task_ = task

    def compose(self) -> ComposeResult:
        with Grid():
            with Middle():
                yield TaskLabel(task=self.task_)
            with Middle():
                yield TaskSelect(task=self.task_)


class TaskLabel(Container):
    task_: Task

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.task_ = task

    def compose(self) -> ComposeResult:
        yield Label(
            self.task_.full_name, classes=f"{self.task_.group_name} {self.task_.name}"
        )

    def on_mount(self) -> None:
        self.query_one(Label).tooltip = self.task_.description


class TaskSelect(Select):
    def __init__(self, task: Task) -> None:
        super().__init__(
            options=[
                (ActionMode.APPLY, ActionMode.APPLY),
                (ActionMode.REVERT, ActionMode.REVERT),
                (ActionMode.SKIP, ActionMode.SKIP),
            ],
            value=(task.mode or ActionMode.SKIP),
            allow_blank=False,
        )
        self.action = task

    def on_focus(self, _: Focus) -> None:
        list_item = self.screen.query_one(
            f".{self.action.group_name}.{self.action.name}", ListItem
        )
        list_view = self.screen.query_one(ListView)
        list_view.index = list_view._nodes.index(list_item)  # noqa: SLF001


if __name__ == "__main__":
    WinconfigApp().run()
