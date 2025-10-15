from sophia_definition import create_definition_container_from_sophia
from winutil_definition import WinutilDefinitionContainer


def main() -> None:
    create_winutil_definition()
    create_sophia_definition()


def create_winutil_definition() -> None:
    winutil = WinutilDefinitionContainer.from_winutil_url(
        definition_url="https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/config/tweaks.json",
        preload_script_urls=[
            "https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/functions/private/Invoke-WinUtilExplorerUpdate.ps1",
            "https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/functions/public/Invoke-WPFRunspace.ps1",
        ],
    )
    winutil.to_winconfig_definition().output_yaml(
        "src/winconfig/definitions/winutil_definition.yaml"
    )


def create_sophia_definition() -> None:
    sophia = create_definition_container_from_sophia(
        definition_url="https://raw.githubusercontent.com/farag2/Sophia-Script-for-Windows/refs/heads/master/src/Sophia_Script_for_Windows_11/Sophia.ps1",
        preload_script_urls=[
            "https://raw.githubusercontent.com/farag2/Sophia-Script-for-Windows/refs/heads/master/src/Sophia_Script_for_Windows_11/Module/Sophia.psm1",
        ],
    )
    sophia.output_yaml("src/winconfig/definitions/sophia_definition.yaml")


main()
