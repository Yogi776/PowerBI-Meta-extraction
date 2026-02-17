param(
    [string]$PbixPath = "PowerBI Examples\Territory Tracker -Slim.pbix",
    [string]$OutRoot = "out\territory-slim\windows-extract",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Resolve-ToolPath {
    $cmd = Get-Command "pbi-tools" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $localExe = Join-Path $PSScriptRoot "..\out\tools\pbi-tools-desktop\pbi-tools.exe"
    $localExe = [System.IO.Path]::GetFullPath($localExe)
    if (Test-Path $localExe) { return $localExe }

    throw "Could not find 'pbi-tools'. Install it or place pbi-tools.exe at '$localExe'."
}

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$pbixFull = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $PbixPath))

if (-not (Test-Path $pbixFull)) {
    throw "PBIX file not found: $pbixFull"
}

$outRootFull = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutRoot))
$legacyFolder = Join-Path $outRootFull "legacy"

if ((Test-Path $outRootFull) -and $Force) {
    Remove-Item -Recurse -Force $outRootFull
}

New-Item -ItemType Directory -Path $legacyFolder -Force | Out-Null

$tool = Resolve-ToolPath
Write-Host "Using pbi-tools at: $tool"
Write-Host "PBIX: $pbixFull"
Write-Host "Output root: $outRootFull"

# 1) Extract PBIX with Legacy model serialization (creates .dax files for model objects)
& $tool extract $pbixFull -extractFolder $legacyFolder -modelSerialization Legacy
if ($LASTEXITCODE -ne 0) {
    throw "pbi-tools extract failed with exit code $LASTEXITCODE"
}

# 2) Generate BIM from extracted folder (output is derived from folder name)
& $tool generate-bim $legacyFolder
if ($LASTEXITCODE -ne 0) {
    throw "pbi-tools generate-bim failed with exit code $LASTEXITCODE"
}

# 3) Produce a simple DAX index file
$daxFiles = Get-ChildItem -Path $legacyFolder -Recurse -Filter "*.dax" | Sort-Object FullName
$indexPath = Join-Path $outRootFull "dax-index.txt"
$daxFiles | ForEach-Object { $_.FullName } | Set-Content -Path $indexPath -Encoding UTF8

Write-Host ""
Write-Host "Done."
Write-Host "Legacy extract folder: $legacyFolder"
Write-Host "DAX index: $indexPath"
Write-Host "DAX files found: $($daxFiles.Count)"

# generate-bim writes ../<foldername>.bim relative to the folder argument
$bimPath = Join-Path (Split-Path $legacyFolder -Parent) ("{0}.bim" -f (Split-Path $legacyFolder -Leaf))
if (Test-Path $bimPath) {
    Write-Host "BIM file: $bimPath"
} else {
    Write-Warning "BIM file was not found at expected path: $bimPath"
}
