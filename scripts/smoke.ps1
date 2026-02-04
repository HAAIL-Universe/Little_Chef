param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$BearerToken
)

$ErrorActionPreference = "Stop"
$fail = $false

function Show-Result($name, $resp) {
  if ($null -eq $resp) { Write-Host "[$name] no response" -ForegroundColor Red; $global:fail = $true; return }
  Write-Host ("[{0}] {1}" -f $name, $resp.StatusCode) -ForegroundColor Cyan
  try {
    $body = $resp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($body) { $body | ConvertTo-Json -Depth 4 }
  } catch { }
  if ($resp.StatusCode -ge 400) { $global:fail = $true }
}

function Hit($name, $url, $headers=@{}) {
  try {
    $resp = Invoke-WebRequest -Method Get -Uri $url -Headers $headers -ErrorAction Stop
  } catch {
    $resp = $_.Exception.Response
  }
  Show-Result $name $resp
}

Hit 'health' "$BaseUrl/health"
Hit 'docs' "$BaseUrl/docs"
Hit 'openapi' "$BaseUrl/openapi.json"

if ($BearerToken) {
  Hit 'auth/me' "$BaseUrl/auth/me" @{ Authorization = "Bearer $BearerToken" }
} else {
  Hit 'auth/me (no token)' "$BaseUrl/auth/me"
}

if ($fail) { exit 1 } else { exit 0 }
