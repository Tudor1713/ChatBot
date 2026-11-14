param([string]$OutputDirectory = 'outputs/build')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install requirements first.' }
$buildOutput = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $OutputDirectory))
if (-not $buildOutput.StartsWith($projectRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Build output must stay inside this project.' }
$appOutput = Join-Path $buildOutput 'ChatBot'
if (Test-Path -LiteralPath (Join-Path $appOutput 'data')) { throw 'This destination contains user data; select a fresh build output.' }
& $pythonPath scripts/fetch_font.py
if ($LASTEXITCODE -ne 0) { throw 'Font verification failed.' }
& $pythonPath scripts/check_secrets.py --tree .
if ($LASTEXITCODE -ne 0) { throw 'Source privacy check failed.' }
$gitExecutable = Get-Command git -ErrorAction SilentlyContinue
$runtimePaths = @((Split-Path -Parent $pythonPath), ($env:SystemRoot + '\System32'), $env:SystemRoot)
if ($gitExecutable) { $runtimePaths += Split-Path -Parent $gitExecutable.Source }
$env:PATH = $runtimePaths -join ';'
& $pythonPath -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $pythonPath -m PyInstaller --clean --noconfirm --distpath $buildOutput --workpath work\build ChatBot.spec
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
Copy-Item -LiteralPath (Join-Path $projectRoot 'README.md') -Destination (Join-Path $appOutput 'README.md')
Copy-Item -LiteralPath (Join-Path $projectRoot 'LICENSE') -Destination (Join-Path $appOutput 'LICENSE')
Copy-Item -LiteralPath (Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') -Destination (Join-Path $appOutput 'THIRD_PARTY_NOTICES.md')
Copy-Item -LiteralPath (Join-Path $projectRoot 'docs') -Destination (Join-Path $appOutput 'docs') -Recurse
New-Item -ItemType Directory -Path (Join-Path $appOutput 'licenses') -Force | Out-Null
& $pythonPath scripts/collect_licenses.py --output (Join-Path $appOutput 'licenses/runtime')
Write-Output ('Portable build ready: ' + $appOutput)
