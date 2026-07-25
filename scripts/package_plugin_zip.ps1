# Build an Agent Zero-ready plugin ZIP: a0_pen_paper/plugin.yaml inside the archive folder.
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Dist = Join-Path $Root "dist"
$Stage = Join-Path $Dist "stage"
$PluginDir = Join-Path $Stage "a0_pen_paper"
$Out = Join-Path $Dist "a0_pen_paper.zip"

if (Test-Path $Stage) {
    Remove-Item $Stage -Recurse -Force
}
New-Item -ItemType Directory -Path $PluginDir -Force | Out-Null

$ExcludeDirs = @(".git", ".github", "__pycache__", ".pytest_cache", "dist", "usr")
$ExcludeFiles = @("config.json")

Get-ChildItem -Path $Root -Force | ForEach-Object {
    if ($ExcludeDirs -contains $_.Name) { return }
    if ($_.Name -like ".toggle-*") { return }
    if ($_.Name -eq "docs" -and (Test-Path (Join-Path $_.FullName "dev-tracker.html"))) {
        $docsDest = Join-Path $PluginDir "docs"
        New-Item -ItemType Directory -Path $docsDest -Force | Out-Null
        Get-ChildItem -Path $_.FullName -Force | Where-Object { $_.Name -ne "dev-tracker.html" } |
            Copy-Item -Destination $docsDest -Recurse -Force
        return
    }
    if ($ExcludeFiles -contains $_.Name) { return }
    Copy-Item -Path $_.FullName -Destination $PluginDir -Recurse -Force
}

if (Test-Path $Out) {
    Remove-Item $Out -Force
}
New-Item -ItemType Directory -Path $Dist -Force | Out-Null
Compress-Archive -Path $PluginDir -DestinationPath $Out -Force

Write-Host "Created $Out"
