$ErrorActionPreference = 'Stop'
$handoffPython = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $handoffPython) {
    & $handoffPython.Source (Join-Path $PSScriptRoot 'START.py')
} else {
    $handoffLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -eq $handoffLauncher) { throw 'Install Python 3.10 or later, then run START.py.' }
    & $handoffLauncher.Source -3 (Join-Path $PSScriptRoot 'START.py')
}
exit $LASTEXITCODE
