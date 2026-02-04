param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$BearerToken
)

$ErrorActionPreference = "Stop"

$results = @()

function Make-Result([string]$Name, [string]$Url, [int]$Expected, [int]$Status, [string]$BodySnippet, [string]$Error) {
  $ok = $Status -eq $Expected
  return [pscustomobject]@{
    Name        = $Name
    Url         = $Url
    Expected    = $Expected
    StatusCode  = $Status
    Ok          = $ok
    BodySnippet = $BodySnippet
    Error       = $Error
  }
}

function Invoke-Check {
  param(
    [string]$Name,
    [string]$Path,
    [int]$ExpectedStatus,
    [hashtable]$Headers = @{},
    [switch]$SkipBody
  )
  $url = "$BaseUrl$Path"
  $status = 0
  $bodySnippet = ""
  $err = ""

  try {
    $resp = Invoke-WebRequest -Method Get -Uri $url -Headers $Headers -TimeoutSec 20 -ErrorAction Stop
    $status = [int]$resp.StatusCode
    if (-not $SkipBody) {
      $content = $resp.Content
      if ($content) {
        if ($content.Length -gt 300) { $content = $content.Substring(0,300) }
        $bodySnippet = $content
      }
    }
  }
  catch {
    $ex = $_.Exception
    if ($ex.Response) {
      $statusObj = $ex.Response.StatusCode
      if ($statusObj) { $status = [int]$statusObj }
      try {
        $reader = New-Object System.IO.StreamReader($ex.Response.GetResponseStream())
        $text = $reader.ReadToEnd()
        if ($text.Length -gt 300) { $text = $text.Substring(0,300) }
        $bodySnippet = $text
      } catch { }
    } else {
      $status = 0
      $err = $ex.Message
    }
  }

  $result = Make-Result -Name $Name -Url $url -Expected $ExpectedStatus -Status $status -BodySnippet $bodySnippet -Error $err
  $script:results += $result
}

Invoke-Check -Name "health" -Path "/health" -ExpectedStatus 200
Invoke-Check -Name "docs" -Path "/docs" -ExpectedStatus 200
Invoke-Check -Name "openapi" -Path "/openapi.json" -ExpectedStatus 200 -SkipBody

# Auth behavior
Invoke-Check -Name "auth/me (no token)" -Path "/auth/me" -ExpectedStatus 401
if ($BearerToken) {
  Invoke-Check -Name "auth/me (token)" -Path "/auth/me" -ExpectedStatus 200 -Headers @{ Authorization = "Bearer $BearerToken" }
}

$anyFail = $false
foreach ($r in $results) {
  $color = if ($r.Ok) { "Green" } else { $anyFail = $true; "Red" }
  $msg = "[{0}] {1} (expected {2})" -f $r.Name, $r.StatusCode, $r.Expected
  if ($r.BodySnippet) { $msg += " body: " + ($r.BodySnippet.Replace("`r","").Replace("`n"," ")) }
  if ($r.Error) { $msg += " error: " + $r.Error }
  Write-Host $msg -ForegroundColor $color
}

if ($anyFail) { exit 1 } else { exit 0 }
