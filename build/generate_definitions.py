from sophia_definition import SophiaDefinition
from winutil_definition import WinutilDefinition


def main() -> None:
    create_winutil_definition()
    create_sophia_definition()


def create_winutil_definition() -> None:
    winutil_definition = WinutilDefinition.pull()
    definition = winutil_definition.convert()
    definition.output_yaml("src/winconfig/definitions/winutil.definition.yaml")


def create_sophia_definition() -> None:
    sophia_definition = SophiaDefinition.pull()
    definition = sophia_definition.convert()
    definition.output_yaml("src/winconfig/definitions/sophia.definition.yaml")


main()
