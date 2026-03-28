param(
    [string]$Python = "python",
    [string]$NodePackageManager = "npm.cmd"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Push-Location (Join-Path $root "mock-salesforce-mcp")
try {
    & $Python -m pip install -e .[dev]
}
finally {
    Pop-Location
}

Push-Location (Join-Path $root "salesforce-agent")
try {
    & $Python -m pip install -e .[dev]
}
finally {
    Pop-Location
}

Push-Location (Join-Path $root "salesforce-agent-ui")
try {
    & $NodePackageManager install
}
finally {
    Pop-Location
}

Write-Host "Setup complete."

