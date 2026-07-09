param(
  [string]$Output = "$env:USERPROFILE\Desktop\lumia-scriptor-rag-deploy.zip"
)

$ErrorActionPreference = "Stop"

$repo = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$temp = Join-Path $env:TEMP ("lumia-scriptor-rag-package-" + [guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Force -Path $temp | Out-Null

$excludeDirs = @(
  ".git",
  "frontend\node_modules",
  "frontend\dist",
  "runtime",
  "uploads",
  "build",
  "dist",
  "deploy\data"
)

robocopy $repo $temp /E /XD $excludeDirs /XF "*.log" "*.tmp" "*.pyc" "*.pyo" "*.zip" | Out-Null

if (Test-Path $Output) {
  Remove-Item $Output -Force
}

Compress-Archive -Path (Join-Path $temp "*") -DestinationPath $Output -Force
Remove-Item $temp -Recurse -Force

Write-Host "Package created: $Output"
