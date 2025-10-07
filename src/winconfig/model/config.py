from pydantic import RootModel


class Config(RootModel):
    root: str

    @property
    def name(self) -> str:
        return self.root

    @property
    def revert(self) -> bool:
        return False


class ConfigContainer(RootModel):
    root: list[Config] = []
