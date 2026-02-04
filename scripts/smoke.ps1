param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [string]$Jwt
)

function Show-Result($name, $resp) {
  if ($null -eq $resp) { Write-Host "[$name] no response" -ForegroundColor Red; return }
  Write-Host ("[{0}] {1}" -f $name, $resp.StatusCode) -ForegroundColor Cyan
  try {
    $body = $resp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($body) { $body | ConvertTo-Json -Depth 4 }
  } catch { }
}

# health or openapi
$healthUrl = "$BaseUrl/health"
try {
  $resp = Invoke-WebRequest -Method Get -Uri $healthUrl -ErrorAction Stop
  Show-Result "health" $resp
} catch {
  $resp = $null
  Write-Host "[health] failed, trying /openapi.json" -ForegroundColor Yellow
  try {
    $resp = Invoke-WebRequest -Method Get -Uri "$BaseUrl/openapi.json" -ErrorAction Stop
    Show-Result "openapi" $resp
  } catch {
    Write-Host "[openapi] failed" -ForegroundColor Red
  }
}

if ($Jwt) {
  try {
    $resp = Invoke-WebRequest -Method Get -Uri "$BaseUrl/auth/me" -Headers @{ Authorization = "Bearer $Jwt" } -ErrorAction Stop
  } catch {
    $resp = $_.Exception.Response
  }
  Show-Result "auth/me" $resp
}
