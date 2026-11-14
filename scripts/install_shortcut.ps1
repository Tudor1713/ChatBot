param([Parameter(Mandatory=$true)][string]$InstallDirectory)
$ErrorActionPreference = 'Stop'
$applicationDirectory = (Resolve-Path -LiteralPath $InstallDirectory).Path
$executable = Join-Path $applicationDirectory 'ChatBot.exe'
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) { throw 'ChatBot.exe is missing.' }
$desktopDirectory = [Environment]::GetFolderPath('DesktopDirectory')
if (-not (Test-Path -LiteralPath $desktopDirectory -PathType Container)) { throw 'Desktop directory is missing.' }
$shell = New-Object -ComObject WScript.Shell
$destinations = @((Join-Path $desktopDirectory 'ChatBot.lnk'), (Join-Path (Split-Path -Parent $applicationDirectory) 'ChatBot.lnk'))
foreach ($destination in $destinations) {
    $shortcut = $shell.CreateShortcut($destination)
    $shortcut.TargetPath = $executable
    $shortcut.WorkingDirectory = $applicationDirectory
    $shortcut.Arguments = '--start-capture'
    $shortcut.IconLocation = $executable + ',0'
    $shortcut.Description = 'ChatBot'
    $shortcut.Save()
    $verified = $shell.CreateShortcut($destination)
    if ($verified.TargetPath -ne $executable -or -not (Test-Path -LiteralPath $verified.TargetPath)) { throw 'Shortcut verification failed.' }
    Write-Output ('Verified: ' + $destination)
}
