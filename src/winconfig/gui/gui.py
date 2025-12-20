from pathlib import Path
from typing import Any, ClassVar, cast

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

    engine: Engine

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.engine = Engine()
        self.engine.config.merge(Path("samples/winconfig.config.yaml"))

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            yield TaskList()
        yield Footer()


class TaskList(ListView):
    BORDER_TITLE = "TaskList"

    BINDINGS: ClassVar = [
        ("a", f"set_action_mode('{ActionMode.APPLY}')", "Set apply mode"),
        ("r", f"set_action_mode('{ActionMode.REVERT}')", "Set revert mode"),
        ("s", f"set_action_mode('{ActionMode.SKIP}')", "Set skip mode"),
    ]

    def __init__(self) -> None:
        super().__init__(
            *[
                TaskListItem(task=task)
                for group in cast(WinconfigApp, self.app).engine.task_groups
                for task in group.tasks
            ],
        )

    def action_set_action_mode(self, mode: ActionMode) -> None:
        selected_line = self.screen.query_one(".-highlight", ListItem)
        selected_line.query_one(TaskSelect).value = mode


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
        self.task_ = task

    def on_focus(self, _: Focus) -> None:
        list_item = self.screen.query_one(
            f".{self.task_.group_name}.{self.task_.name}", ListItem
        )
        list_view = self.screen.query_one(ListView)
        list_view.index = list_view._nodes.index(list_item)  # noqa: SLF001

    def watch_value(self, old_value: str, new_value: str) -> None:
        list_item = self.screen.query_one(
            f".{self.task_.group_name}.{self.task_.name}", ListItem
        )
        if old_value != Select.BLANK:
            list_item.remove_class(old_value)
        if new_value != Select.BLANK:
            list_item.add_class(new_value)


if __name__ == "__main__":
    WinconfigApp().run()
