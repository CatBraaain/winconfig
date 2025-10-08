param([string]$Headless = $true)

[bool]$isHeadless = $false
[bool]::TryParse($val, [ref]$isHeadless) | Out-Null

$runAs = $(if ($isHeadless) { "System" } else { "ExistingLogin" })

wsb stop --id (wsb list)
echo "Opening sandbox ${id}"
$id = (wsb start --raw | ConvertFrom-Json).Id
wsb share --id $id --host-path . --sandbox-path %UserProfile%\winconfig --allow-write

if (!$isHeadless) {
    echo "Logging into sandbox"
    wsb connect --id $id
    do {
        wsb exec --id $id --command "whoami" --run-as $runAs 2>&1 | Out-Null
    } while (!$?)
}

echo "Installing uv"
$command = "powershell -ExecutionPolicy ByPass -c """"irm https://astral.sh/uv/install.ps1 | iex"""""
wsb exec --id $id --command $command --run-as $runAs

# $command = "uv run pytest %UserProfile%/winconfig"
# wsb exec --id $id --command $command --run-as $runAs
