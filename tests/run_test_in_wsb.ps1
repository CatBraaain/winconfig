param([string]$Headless = $false)

[bool]$isHeadless = $false
[bool]::TryParse($Headless, [ref]$isHeadless) | Out-Null

$runAs = $(if ($isHeadless) { "System" } else { "ExistingLogin" })

wsb stop --id (wsb list) 2>&1 | Out-Null
echo "Opening sandbox ${id}"
$id = (wsb start --raw | ConvertFrom-Json).Id
wsb share --id $id --host-path . --sandbox-path C:\winconfig-readonly

if (!$isHeadless) {
    echo "Logging into sandbox"
    wsb connect --id $id
    do {
        wsb exec --id $id --command "whoami" --run-as $runAs 2>&1 | Out-Null
    } while (!$?)
}

$command = "reg add ""HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy"" /v VerifiedAndReputablePolicyState /t REG_DWORD /d 0 /f"
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs

$command = "CiTool --refresh"
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs

$command = "robocopy C:\winconfig-readonly C:\winconfig /s /xf .* /xd .*"
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs
echo "*hint: exit code 1 is OK"

$command = "powershell -ExecutionPolicy ByPass -c """"irm https://astral.sh/uv/install.ps1 | iex"""""
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs

$command = "uv venv --python 3.13"
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs --working-directory C:\winconfig

$command = "uv sync"
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs --working-directory C:\winconfig

$command = "cmd.exe /c start cmd.exe /k """"uv run pytest --durations 0 -v"""""
echo "> $command"
wsb exec --id $id --command $command --run-as $runAs --working-directory C:\winconfig
