from pydantic import RootModel


class ConfigElement(RootModel):
    root: str

    @property
    def name(self) -> str:
        return self.root

    @property
    def revert(self) -> bool:
        return False


class Config(RootModel):
    root: list[ConfigElement] = []
