from winutil_definition import WinutilDefinitionContainer


def main() -> None:
    create_winutil_definitions()


def create_winutil_definitions() -> None:
    winutil = WinutilDefinitionContainer.from_winutil_url(
        definition_url="https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/config/tweaks.json",
        preload_script_urls=[
            "https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/functions/private/Invoke-WinUtilExplorerUpdate.ps1",
            "https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/functions/public/Invoke-WPFRunspace.ps1",
        ],
    )
    winutil.output_yaml_file("src/winconfig/definitions/winutil_definition.yaml")


main()
