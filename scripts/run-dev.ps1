param(
    [string]$Python = "python",
    [string]$NodePackageManager = "npm.cmd"
)

$root = Split-Path -Parent $PSScriptRoot

Write-Host "Start these in separate terminals:"
Write-Host "1. MCP server"
Write-Host "   cd $root\\mock-salesforce-mcp"
Write-Host "   $Python -m app.server --transport streamable-http"
Write-Host ""
Write-Host "2. Agent backend"
Write-Host "   cd $root\\salesforce-agent"
Write-Host "   Copy-Item .env.example .env"
Write-Host "   $Python -m agents.server"
Write-Host ""
Write-Host "3. UI"
Write-Host "   cd $root\\salesforce-agent-ui"
Write-Host "   $NodePackageManager run dev"

