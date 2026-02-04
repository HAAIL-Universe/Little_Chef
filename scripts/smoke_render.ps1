param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [string]$Jwt,
  [switch]$Verbose
)

function Hit($path) {
  $uri = "$BaseUrl$path"
  try {
    if ($Jwt) {
      $res = Invoke-RestMethod -Method Get -Uri $uri -Headers @{ Authorization = "Bearer $Jwt" } -ErrorAction Stop
      $code = 200
    } else {
      $resp = Invoke-WebRequest -Method Get -Uri $uri -ErrorAction Stop
      $code = $resp.StatusCode
      $res = $resp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    }
    Write-Host "[$path] $code" -ForegroundColor Cyan
    if ($Verbose -and $res) { $res | ConvertTo-Json -Depth 6 }
  } catch {
    $err = $_.Exception
    $code = $_.Exception.Response.StatusCode.Value__ 2>$null
    Write-Host "[$path] FAIL $code" -ForegroundColor Red
    if ($Verbose) { Write-Host $err }
  }
}

Hit "/health"
if ($Jwt) { Hit "/auth/me" }
