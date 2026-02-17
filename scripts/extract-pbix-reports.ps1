<#
.SYNOPSIS
    Extracts all PBIX reports from a folder (or a single report) to legacy format with DAX and BIM.

.DESCRIPTION
    User-defined source folder path and output root. Processes all .pbix files in the source folder,
    or a single file if SourcePath points to a .pbix file. Each report gets its own subfolder under OutRoot.

.PARAMETER SourcePath
    Folder containing .pbix files, or path to a single .pbix file.
    Relative paths are resolved from the repo root (parent of scripts folder).

.PARAMETER OutRoot
    Root folder for generated output. Each report gets: OutRoot\<report-name>\windows-extract\
    Relative paths are resolved from the repo root.

.PARAMETER Force
    If set, overwrites existing output folders for each report.
#>
param(
    [string]$SourcePath = "PowerBI Examples",
    [string]$OutRoot = "out",
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

function Process-Pbix {
    param(
        [string]$PbixFullPath,
        [string]$OutputRootFull,
        [string]$ToolExe,
        [bool]$ForceOverwrite
    )

    $reportName = [System.IO.Path]::GetFileNameWithoutExtension($PbixFullPath)
    $outReportRoot = Join-Path $OutputRootFull $reportName
    $legacyFolder = Join-Path $outReportRoot "windows-extract\legacy"

    if ((Test-Path $outReportRoot) -and $ForceOverwrite) {
        Remove-Item -Recurse -Force $outReportRoot
    }

    New-Item -ItemType Directory -Path $legacyFolder -Force | Out-Null

    Write-Host ""
    Write-Host "--- $reportName ---"
    Write-Host "  PBIX: $PbixFullPath"
    Write-Host "  Output: $outReportRoot"

    # 1) Extract PBIX with Legacy model serialization
    & $ToolExe extract $PbixFullPath -extractFolder $legacyFolder -modelSerialization Legacy | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "pbi-tools extract failed for '$reportName' with exit code $LASTEXITCODE"
    }

    # 2) Generate BIM from extracted folder
    & $ToolExe generate-bim $legacyFolder | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "pbi-tools generate-bim failed for '$reportName' with exit code $LASTEXITCODE"
    }

    # 3) DAX index file
    $daxFiles = Get-ChildItem -Path $legacyFolder -Recurse -Filter "*.dax" -ErrorAction SilentlyContinue | Sort-Object FullName
    $indexPath = Join-Path $outReportRoot "dax-index.txt"
    $daxFiles | ForEach-Object { $_.FullName } | Set-Content -Path $indexPath -Encoding UTF8 | Out-Null

    $bimPath = Join-Path (Split-Path $legacyFolder -Parent) ("{0}.bim" -f (Split-Path $legacyFolder -Leaf))
    Write-Host "  DAX files: $($daxFiles.Count) | Index: $indexPath"
    if (Test-Path $bimPath) {
        Write-Host "  BIM: $bimPath"
    }

    return $reportName
}

# Resolve paths relative to repo root when not absolute
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sourceFull = if ([System.IO.Path]::IsPathRooted($SourcePath)) {
    $SourcePath
} else {
    [System.IO.Path]::GetFullPath((Join-Path $repoRoot $SourcePath))
}
$outRootFull = if ([System.IO.Path]::IsPathRooted($OutRoot)) {
    $OutRoot
} else {
    [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutRoot))
}

# Collect PBIX files: either one file or all in folder
$pbixFiles = @()
if ([System.IO.Path]::GetExtension($sourceFull) -eq ".pbix") {
    if (-not (Test-Path $sourceFull)) {
        throw "PBIX file not found: $sourceFull"
    }
    $pbixFiles = @($sourceFull)
} else {
    if (-not (Test-Path $sourceFull)) {
        throw "Source path not found: $sourceFull"
    }
    $pbixFiles = Get-ChildItem -Path $sourceFull -Filter "*.pbix" -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    if ($pbixFiles.Count -eq 0) {
        throw "No .pbix files found in: $sourceFull"
    }
}

$tool = Resolve-ToolPath
Write-Host "Using pbi-tools: $tool"
Write-Host "Source: $sourceFull"
Write-Host "Output root: $outRootFull"
Write-Host "Reports to process: $($pbixFiles.Count)"

$processed = @()
foreach ($pbix in $pbixFiles) {
    try {
        $name = Process-Pbix -PbixFullPath $pbix -OutputRootFull $outRootFull -ToolExe $tool -ForceOverwrite $Force.IsPresent
        $processed += $name
    } catch {
        Write-Error $_.Exception.Message
        throw
    }
}

Write-Host ""
Write-Host "Done. Processed $($processed.Count) report(s):"
$processed | ForEach-Object { Write-Host "  - $_" }
