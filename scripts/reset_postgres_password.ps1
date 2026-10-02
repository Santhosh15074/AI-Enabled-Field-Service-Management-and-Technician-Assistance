# Resets the password of the local "postgres" user when it has been forgotten.
# Run from an Administrator PowerShell window:
#   powershell -ExecutionPolicy Bypass -File scripts\reset_postgres_password.ps1
#
# How it works: PostgreSQL briefly accepts local connections without a password ("trust"),
# you set a new password, then the original security settings are always restored.

$ErrorActionPreference = "Stop"

$service = "postgresql-x64-18"
$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$hba = "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"
$backup = "$hba.before-reset"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Run this from an Administrator PowerShell window (right-click PowerShell > Run as administrator)." -ForegroundColor Red
    exit 1
}

Copy-Item $hba $backup -Force
try {
    # Allow password-free logins from this computer only (127.0.0.1 and ::1).
    (Get-Content $hba) -replace '^(host\s+all\s+all\s+(127\.0\.0\.1/32|::1/128)\s+)scram-sha-256', '${1}trust' |
        Set-Content $hba -Encoding ascii
    Restart-Service $service

    Write-Host ""
    Write-Host "Type the NEW password for the postgres user (it won't show as you type)." -ForegroundColor Cyan
    & "$pgBin\psql.exe" -U postgres -h localhost -c "\password postgres"
    if ($LASTEXITCODE -ne 0) { throw "Setting the password failed." }
}
finally {
    # Always put the original password rules back.
    Copy-Item $backup $hba -Force
    Remove-Item $backup
    Restart-Service $service
    Write-Host "Original security settings restored." -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Check the new password with:" -ForegroundColor Green
Write-Host "  & `"$pgBin\psql.exe`" -U postgres -h localhost -c `"select 1`""
