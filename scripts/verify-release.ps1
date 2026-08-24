param(
  [Parameter(Mandatory = $true)][string]$PackagePath,
  [Parameter(Mandatory = $true)][string]$ChecksumsPath
)

$ErrorActionPreference = 'Stop'
$package = (Resolve-Path -LiteralPath $PackagePath).Path
$checksums = (Resolve-Path -LiteralPath $ChecksumsPath).Path
$expectedName = [IO.Path]::GetFileName($package)
$line = Get-Content -LiteralPath $checksums -Encoding UTF8 |
  Where-Object { $_ -match ('^[0-9a-fA-F]{64}\s+\*?' + [regex]::Escape($expectedName) + '$') } |
  Select-Object -First 1
if (-not $line) { throw "No checksum entry found for $expectedName" }
$expected = ($line -split '\s+', 2)[0].ToUpperInvariant()
$actual = (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash.ToUpperInvariant()
if ($actual -ne $expected) { throw "SHA-256 mismatch: expected $expected, actual $actual" }
Write-Output "PASS $expectedName SHA-256 $actual"
