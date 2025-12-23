from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from textual.widget import Widget

    from winconfig.gui.app import WinconfigApp


class RootAccessMixin:
    @property
    def root(self: Widget) -> WinconfigApp:
        return cast("WinconfigApp", self.app)
