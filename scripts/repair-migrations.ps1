Param(
    [string]$Dsn = $env:POSTGRES_DSN
)

$ErrorActionPreference = "Stop"

if (-not $Dsn -or $Dsn.Trim() -eq "") {
    $Dsn = "postgresql+psycopg://postgres:postgres@localhost:5432/appdb"
}

Write-Host "Using POSTGRES_DSN = $Dsn"

$services = @("auth","catalog","order")

foreach ($svc in $services) {
    Write-Host ">>> Repairing migrations for service: $svc"
    Push-Location "services\$svc"

    # Ensure Alembic sees the DSN
    $env:POSTGRES_DSN = $Dsn

    try {
        # Reset any bad revision in the DB to 'base'
        Write-Host "  - Stamping DB to base (clears unknown revision)"
        alembic stamp base

        # Now apply all branches to latest
        Write-Host "  - Upgrading to all heads"
        alembic upgrade heads

        # Show resulting head(s)
        Write-Host "  - Current revision(s):"
        alembic current
    }
    finally {
        Pop-Location
    }
}

Write-Host "Done."
