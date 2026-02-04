param(
  [switch]$NoVenv,
  [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-EnvFile {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line) { return }
    if ($line.StartsWith("#")) { return }
    $parts = $line.Split("=", 2)
    if ($parts.Count -lt 2) { return }
    $key = $parts[0].Trim()
    $val = $parts[1].Trim()
    if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Trim('"') }
    elseif ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Trim("'") }
    if (-not $key) { return }
    if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($key))) {
      [Environment]::SetEnvironmentVariable($key, $val)
    }
  }
}

function Info($m) { Write-Host "[db_migrate] $m" -ForegroundColor Cyan }
function Err ($m) { Write-Host "[db_migrate] $m" -ForegroundColor Red }

function Resolve-Python {
  if (-not $NoVenv) {
    $localVenv = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\\Scripts\\python.exe"
    if (Test-Path $localVenv) { return $localVenv }
  }
  return "python"
}

try {
  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
  $envPath = Join-Path $repoRoot ".env"
  Load-EnvFile -Path $envPath

  if (-not $env:DATABASE_URL) {
    Err "DATABASE_URL not set; set it in .env or the environment before running migrations."
    exit 1
  } else {
    Info "DATABASE_URL present (value not printed)."
  }

  if ($ValidateOnly) {
    $sqlPath = Join-Path $repoRoot "db/migrations/0001_init.sql"
    if (-not (Test-Path $sqlPath)) {
      Err "Migration file not found at $sqlPath"
      exit 1
    }
    Info ".env load check complete; migration file exists. ValidateOnly exiting."
    exit 0
  }

  $py = Resolve-Python
  Info "Python: $py"
  Push-Location $repoRoot
  try {
    $out = & $py -m app.db.migrate 2>&1
    if ($LASTEXITCODE -ne 0) {
      $text = $out | Out-String
      if ($text -match "schema_migrations_pkey" -and $text -match "duplicate key") {
        Info "Migration already applied (duplicate schema_migrations entry); treating as success."
        return
      } else {
        Write-Host $text
        throw "Migration failed ($LASTEXITCODE)"
      }
    }
    if ($out) { $out | Write-Host }

    # Post-check: ensure users table exists; if missing, re-apply base migration SQL directly (idempotent).
    $checkScript = @"
import os, psycopg
conn = psycopg.connect(os.environ[""DATABASE_URL""])
with conn.cursor() as cur:
    cur.execute(""""select to_regclass('public.users')"""")
    exists = cur.fetchone()[0]
print("USERS_OK" if exists else "USERS_MISSING")
conn.close()
"@
    $tmpCheck = New-TemporaryFile
    Set-Content -Path $tmpCheck -Value $checkScript -Encoding utf8
    $checkOut = & $py $tmpCheck
    Remove-Item $tmpCheck -ErrorAction SilentlyContinue
    if ($checkOut -notlike "*USERS_OK*") {
      Info "users table missing; re-applying db/migrations/0001_init.sql directly (idempotent)."
      $sqlPath = Join-Path $repoRoot "db/migrations/0001_init.sql"
      $applyScript = @"
import os, psycopg
from pathlib import Path
sql = Path(r"$sqlPath").read_text(encoding="utf-8")
conn = psycopg.connect(os.environ[""DATABASE_URL""])
with conn.cursor() as cur:
    cur.execute(sql)
conn.commit()
conn.close()
print("SQL_APPLIED")
"@
      $tmpApply = New-TemporaryFile
      Set-Content -Path $tmpApply -Value $applyScript -Encoding utf8
      $applyOut = & $py $tmpApply
      Remove-Item $tmpApply -ErrorAction SilentlyContinue
      if ($applyOut -notlike "*SQL_APPLIED*") {
        throw "Re-apply of 0001_init.sql did not complete."
      }
      Info "users table created via direct SQL apply."
    }
  }
  finally {
    Pop-Location
  }
}
catch {
  Err $_.Exception.Message
  exit 1
}

exit 0
