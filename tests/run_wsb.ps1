param([string]$Headless = $true)

[bool]$isHeadless = $false
[bool]::TryParse($val, [ref]$isHeadless) | Out-Null

$runAs = $(if ($isHeadless) { "System" } else { "ExistingLogin" })

wsb stop --id (wsb list)
$id = (wsb start --raw | ConvertFrom-Json).Id
echo "Opened sandbox ${id}"
wsb share --id $id --host-path . --sandbox-path %UserProfile%\winconfig

if (!$isHeadless) {
    wsb connect --id $id
    do {
        wsb exec --id $id --command "whoami" --run-as $runAs 2>&1 | Out-Null
    } while (!$?)
    echo "Logged in"
}

$command = "powershell -ExecutionPolicy ByPass -c """"irm https://astral.sh/uv/install.ps1 | iex"""""
wsb exec --id $id --command $command --run-as $runAs
echo "Installed uv"
