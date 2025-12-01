from pydantic import RootModel


class Config(RootModel):
    root: str

    @property
    def name(self) -> str:
        return self.root


class ConfigContainer(RootModel):
    root: list[Config] = []
