# scripts/seed.ps1
$ErrorActionPreference = "Stop"

# --- Figure out repo root ---
$Here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Root = Resolve-Path (Join-Path $Here "..")
Set-Location $Root

# --- Ensure POSTGRES_DSN is set for Alembic (PowerShell doesn't read deploy/.env automatically) ---
if (-not $env:POSTGRES_DSN -or [string]::IsNullOrWhiteSpace($env:POSTGRES_DSN)) {
  $dotenvPath = Join-Path $Root "deploy\.env"
  $dsn = $null

  if (Test-Path $dotenvPath) {
    $line = Select-String -Path $dotenvPath -Pattern '^\s*POSTGRES_DSN\s*=' | Select-Object -First 1
    if ($line) {
      $raw = $line.Line.Split('=')[1].Trim()
      if ($raw.StartsWith('"') -and $raw.EndsWith('"')) { $raw = $raw.Substring(1, $raw.Length-2) }
      if ($raw.StartsWith("'") -and $raw.EndsWith("'")) { $raw = $raw.Substring(1, $raw.Length-2) }
      $dsn = $raw
    }
  }

  if (-not $dsn -or [string]::IsNullOrWhiteSpace($dsn)) {
    $dsn = "postgresql+psycopg://postgres:postgres@localhost:5432/appdb"
  }

  # If DSN points to the Docker service hostname, rewrite to localhost for host tooling
  $dsn = $dsn -replace '@postgres:', '@localhost:'

  $env:POSTGRES_DSN = $dsn
}
Write-Host "Using POSTGRES_DSN = $($env:POSTGRES_DSN)"
Write-Host ">>> Running Alembic migrations"

# --- Auth ---
Set-Location "services/auth"
alembic upgrade heads
Set-Location $Root

# --- Catalog ---
Set-Location "services/catalog"
alembic upgrade heads
Set-Location $Root

# --- Order ---
Set-Location "services/order"
alembic upgrade heads
Set-Location $Root

Set-Location $Root
Write-Host "Done."
