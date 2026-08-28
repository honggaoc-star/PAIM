[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SettingsPath
)

$ErrorActionPreference = 'Stop'

function Show-PaimLaunchError {
    param([string]$Message)

    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        $Message,
        'Practical AI Management',
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
}

try {
    $resolvedSettings = (Resolve-Path -LiteralPath $SettingsPath).Path
    $settings = Get-Content -LiteralPath $resolvedSettings -Raw | ConvertFrom-Json
    $repositoryPath = (Resolve-Path -LiteralPath ([string]$settings.repository_path)).Path
    $configurationPath = (Resolve-Path -LiteralPath ([string]$settings.configuration_path)).Path
    $uvCommand = Get-Command uv -ErrorAction Stop

    Set-Location -LiteralPath $repositoryPath
    & $uvCommand.Source run --locked paim-launcher --config $configurationPath
    if ($LASTEXITCODE -ne 0) {
        throw 'PAIM did not start. Support details are available in the PAIM local application-data logs folder.'
    }
}
catch {
    Show-PaimLaunchError -Message ([string]$_.Exception.Message)
    exit 1
}
