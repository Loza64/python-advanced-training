param(
  [string]$BackupDirectory = ".\backups"
)

$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) {
  throw "DATABASE_URL is required. Load the production secret into the environment first."
}

New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputFile = Join-Path $BackupDirectory "products-$timestamp.dump"

pg_dump $env:DATABASE_URL --format=custom --file=$outputFile --no-owner --no-privileges
Write-Output "Backup created: $outputFile"
