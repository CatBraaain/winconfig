from sophia_definition import SophiaDefinition
from winutil_definition import WinutilDefinition


def main() -> None:
    create_winutil_definition()
    create_sophia_definition()


def create_winutil_definition() -> None:
    winutil_definition = WinutilDefinition.from_remote(
        definition_url="https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/config/tweaks.json",
        preload_script_urls=[],
    )
    winutil_definition.for_winconfig().output_yaml(
        "src/winconfig/definitions/winutil.definition.yaml"
    )


def create_sophia_definition() -> None:
    sophia_definition = SophiaDefinition.from_remote(
        definition_url="https://raw.githubusercontent.com/farag2/Sophia-Script-for-Windows/refs/heads/master/src/Sophia_Script_for_Windows_11/Sophia.ps1",
        preload_script_urls=[
            "https://raw.githubusercontent.com/farag2/Sophia-Script-for-Windows/refs/heads/master/src/Sophia_Script_for_Windows_11/Module/Sophia.psm1",
        ],
    )
    sophia_definition.for_winconfig().output_yaml(
        "src/winconfig/definitions/sophia.definition.yaml"
    )


main()
