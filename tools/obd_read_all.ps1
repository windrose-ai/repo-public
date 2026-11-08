# Windrose OBD read-all for Windows (PowerShell). Read only.
#
#   irm https://raw.githubusercontent.com/windrose-ai/repo-public/main/tools/obd_read_all.ps1 | iex
#
# For CAN FD instead of classic CAN, first run:  $env:WR_OBD_FD = "1"
#
# Needs: the PEAK driver (peak-system.com), the PEAK adapter on the truck's OBD
# port, ignition ON, PCAN-View closed. Installs nothing system-wide: a private
# Python goes into %USERPROFILE%\windrose-obd\python if none is found.

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"

$ref  = if ($env:WR_OBD_REF) { $env:WR_OBD_REF } else { "main" }
$base = "https://raw.githubusercontent.com/windrose-ai/repo-public/$ref/tools"
$dir  = Join-Path $env:USERPROFILE "windrose-obd"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Set-Location $dir

Write-Host "Windrose OBD read-all (read only). Folder: $dir"

if (-not (Test-Path "C:\Windows\System32\PCANBasic.dll")) {
    Write-Host "The PEAK driver is not installed. Install it from https://www.peak-system.com (Support > Drivers), re-plug the adapter, and run this again." -ForegroundColor Yellow
    return
}

# A Python that really runs (the Microsoft Store stub does not count).
$py = $null
foreach ($c in @("py", "python")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
        try { & $c -c "import sys; assert sys.version_info >= (3, 8)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch {}
    }
}
$private = Join-Path $dir "python\python.exe"
if (-not $py -and (Test-Path $private)) { $py = $private }
if (-not $py) {
    Write-Host "Getting a private Python (about 10 MB, one time)..."
    $zip = Join-Path $dir "python.zip"
    Invoke-WebRequest "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip" -OutFile $zip -UseBasicParsing
    Expand-Archive $zip -DestinationPath (Join-Path $dir "python") -Force
    Remove-Item $zip
    $pth = Get-ChildItem (Join-Path $dir "python") -Filter "python3*._pth" | Select-Object -First 1
    (Get-Content $pth.FullName) -replace "^#\s*import site", "import site" | Set-Content $pth.FullName
    Invoke-WebRequest "https://bootstrap.pypa.io/get-pip.py" -OutFile (Join-Path $dir "get-pip.py") -UseBasicParsing
    & $private (Join-Path $dir "get-pip.py") --no-warn-script-location -q
    $py = $private
}

& $py -m pip install -q --disable-pip-version-check --no-warn-script-location "python-can>=4.3"
Invoke-WebRequest "$base/obd_read_all.py" -OutFile (Join-Path $dir "obd_read_all.py") -UseBasicParsing

$args2 = @("obd_read_all.py", "--out", $dir)
if ($env:WR_OBD_FD -eq "1") { $args2 += "--fd" }
& $py @args2

Write-Host ""
Write-Host "Send the newest obd-read-*.asc and obd-read-*.txt from this folder to Windrose." -ForegroundColor Green
Start-Process explorer.exe $dir
