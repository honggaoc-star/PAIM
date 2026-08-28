[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigurationPath,

    [string]$ShortcutPath = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Practical AI Management.lnk')
)

$ErrorActionPreference = 'Stop'
$repositoryPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$launcherPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'Start-PAIM.ps1')).Path
$resolvedConfiguration = (Resolve-Path -LiteralPath $ConfigurationPath).Path
$applicationRoot = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'PAIM'
$settingsPath = Join-Path $applicationRoot 'launcher.json'
$null = New-Item -ItemType Directory -Path $applicationRoot -Force

$settings = [ordered]@{
    repository_path = $repositoryPath
    configuration_path = $resolvedConfiguration
} | ConvertTo-Json
[System.IO.File]::WriteAllText(
    $settingsPath,
    $settings,
    [System.Text.UTF8Encoding]::new($false)
)

$powerShellPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $powerShellPath -PathType Leaf)) {
    throw 'Windows PowerShell is unavailable, so the PAIM desktop shortcut cannot be created.'
}
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $powerShellPath
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcherPath`" -SettingsPath `"$settingsPath`""
$shortcut.WorkingDirectory = $repositoryPath
$shortcut.Description = 'Start Practical AI Management'
$shortcut.Save()

Write-Output "PAIM desktop shortcut created: $ShortcutPath"
Write-Output 'The shortcut stores paths only. It does not store the PAIM credential.'
