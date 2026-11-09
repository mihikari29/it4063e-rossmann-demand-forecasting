param(
    [Parameter(Mandatory = $true)][string]$PresentationPath,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$taskPresentation = (Resolve-Path -LiteralPath $PresentationPath).Path
if ([IO.Path]::GetExtension($taskPresentation) -ne '.pptx') { throw 'Only macro-free PPTX is supported.' }
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $taskOutput) { throw 'Choose a new output directory.' }
New-Item -ItemType Directory -Path $taskOutput | Out-Null
$taskPowerPoint = $null
$taskDeck = $null
$taskVersion = $null
try {
    $taskPowerPoint = New-Object -ComObject PowerPoint.Application
    $taskDeck = $taskPowerPoint.Presentations.Open($taskPresentation, -1, 0, 0)
    if ($taskDeck.Slides.Count -ne 15) { throw 'Expected exactly fifteen slides.' }
    $taskDeck.Export($taskOutput, 'PNG', 1600, 900)
    $taskDeck.SaveAs((Join-Path $taskOutput 'rossmann_presentation.pdf'), 32)
    $taskVersion = $taskPowerPoint.Version
    $taskVersion | Set-Content -LiteralPath (Join-Path $taskOutput 'powerpoint-version.txt')
}
finally {
    if ($null -ne $taskDeck) { $taskDeck.Close(); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDeck) }
    if ($null -ne $taskPowerPoint) { $taskPowerPoint.Quit(); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskPowerPoint) }
}
$taskRepo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$taskHashes = [ordered]@{}
Get-ChildItem -LiteralPath $taskOutput -File | ForEach-Object {
    $taskHashes[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
$taskManifest = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString('o')
    command = @('scripts/render_presentation.ps1', '-PresentationPath', $PresentationPath, '-OutputDirectory', $OutputDirectory)
    configuration = @{ slides = 15; png_width = 1600; png_height = 900 }
    seed = $null
    code_revision = (& git -C $taskRepo rev-parse HEAD)
    lock_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'uv.lock') -Algorithm SHA256).Hash.ToLowerInvariant()
    generator_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    environment = @{ powerpoint = $taskVersion; powershell = $PSVersionTable.PSVersion.ToString() }
    source_sha256 = @{ presentation = (Get-FileHash -LiteralPath $taskPresentation -Algorithm SHA256).Hash.ToLowerInvariant() }
    output_sha256 = $taskHashes
    visual_review = 'Separate page-by-page inspection required; rendering alone is not visual acceptance.'
}
[IO.File]::WriteAllText((Join-Path $taskOutput 'manifest.json'), ($taskManifest | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
