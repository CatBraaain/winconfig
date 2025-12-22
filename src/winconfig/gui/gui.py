from pathlib import Path
from typing import Any, ClassVar, cast

from loguru import logger
from textual.app import App, ComposeResult
from textual.containers import Center, Container, Grid, Middle
from textual.events import Focus
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Log,
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


class RootAccessMixin:
    @property
    def root(self: Widget) -> WinconfigApp:
        return cast(WinconfigApp, self.app)


class RunButton(RootAccessMixin, Button):
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
        except Exception as e:
            self.app.screen.query_one(Log).write(str(e))


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
        selected_line = self.highlighted_child
        if selected_line:
            selected_line.query_one(TaskSelect).value = mode


class TaskListItem(ListItem):
    winconfig_task: Task

    def __init__(self, task: Task) -> None:
        super().__init__(classes=f"{task.group_name} {task.name}")
        self.winconfig_task = task

    def compose(self) -> ComposeResult:
        with Grid():
            with Middle():
                yield TaskLabel(task=self.winconfig_task)
            with Middle():
                yield TaskSelect(task=self.winconfig_task)


class TaskLabel(Container):
    winconfig_task: Task

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.winconfig_task = task

    def compose(self) -> ComposeResult:
        yield Label(
            self.winconfig_task.full_name,
            classes=f"{self.winconfig_task.group_name} {self.winconfig_task.name}",
        )

    def on_mount(self) -> None:
        self.query_one(Label).tooltip = self.winconfig_task.description


class TaskSelect(RootAccessMixin, Select):
    winconfig_task: Task

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
        self.winconfig_task = task

    def on_focus(self, _: Focus) -> None:
        list_item = self.screen.query_one(
            f".{self.winconfig_task.group_name}.{self.winconfig_task.name}", ListItem
        )
        list_view = self.screen.query_one(ListView)
        list_view.index = list_view._nodes.index(list_item)  # noqa: SLF001

    def watch_value(self, old_value: str, new_value: str) -> None:
        if old_value != Select.BLANK:
            self.remove_class(old_value)
        if new_value != Select.BLANK:
            self.add_class(new_value)
            self.root.engine.config.action_config.root[self.winconfig_task.group_name][
                self.winconfig_task.name
            ] = cast(ActionMode, new_value)


if __name__ == "__main__":
    WinconfigApp().run()
