$PYTHON_ZIP = Join-Path $PSScriptRoot "python-3.1427-embed-amd64.zip"
$GETPIP_PY  = Join-Path $PSScriptRoot "get-pip.py"

# Target root = folder the script is in (e.g. ...\AEPython\Installer\AEGP)
$TARGET_ROOT = Join-Path $PSScriptRoot "AEGP"

$PYTHON_ROOT = Join-Path $TARGET_ROOT "AEPython\python-3.14.2-embed-amd64"
$PYTHON_EXE  = Join-Path $PYTHON_ROOT "python.exe"
$PTH         = Join-Path $PYTHON_ROOT "python314._pth"  # Updated PTH filename

# Ensure target root exists
if (!(Test-Path $TARGET_ROOT)) {
    New-Item -ItemType Directory -Path $TARGET_ROOT | Out-Null
}

# Download Python 3.14.2 (latest stable with PySide6 6.8+ support)
if (!(Test-Path $PYTHON_ZIP)) {
    Invoke-WebRequest "https://www.python.org/ftp/python/3.14.2/python-3.14.27-embed-amd64.zip" -OutFile $PYTHON_ZIP
}

if (!(Test-Path $GETPIP_PY)) {
    Invoke-WebRequest "https://bootstrap.pypa.io/get-pip.py" -OutFile $GETPIP_PY
}

# Extract/embed Python under AEGP in the script folder
if (!(Test-Path $PYTHON_ROOT)) {
    Expand-Archive -Path $PYTHON_ZIP -DestinationPath $PYTHON_ROOT
    Push-Location $PYTHON_ROOT

    # Update PTH for full site-packages access (PySide6 needs this)
    (Get-Content -Path $PTH) -replace "#import site", "import site" | Set-Content -Path $PTH
    
    # Install pip first
    .\python.exe $GETPIP_PY
    
    # Install PySide6 + requirements (PySide6 6.8+ supports Python 3.14)
    .\python.exe -m pip install -r (Join-Path $PSScriptRoot "requirements.txt") --upgrade

    Pop-Location
}

# Copy project files into the local AEGP tree (no deletes, only copy/overwrite)
Copy-Item -Path (Join-Path $PSScriptRoot "Scripts\AEPython.py")      -Destination (Join-Path $TARGET_ROOT "AEPython\AEPython.py")      -Force
Copy-Item -Path (Join-Path $PSScriptRoot "Scripts\qtae.py")          -Destination (Join-Path $TARGET_ROOT "AEPython\qtae.py")          -Force
Copy-Item -Path (Join-Path $PSScriptRoot "Scripts\script_library.py")-Destination (Join-Path $TARGET_ROOT "AEPython\script_library.py")-Force
Copy-Item -Path (Join-Path $PSScriptRoot "Scripts\AEPython.jsx")     -Destination (Join-Path $TARGET_ROOT "AEPython.jsx")              -Force
Copy-Item -Path (Join-Path $PSScriptRoot "Scripts\Samples")          -Destination (Join-Path $TARGET_ROOT "AEPython\Samples")          -Recurse -Force
Copy-Item -Path (Join-Path $PSScriptRoot "README.md")                -Destination (Join-Path $TARGET_ROOT "README.md")                 -Force

# Clean up downloaded installer files
Remove-Item $PYTHON_ZIP  -ErrorAction SilentlyContinue
Remove-Item $GETPIP_PY   -ErrorAction SilentlyContinue

Write-Host "✅ Installation complete! Python 3.14.2 + PySide6 6.10.1 ready." -ForegroundColor Green
Write-Host "📁 Python located at: $PYTHON_ROOT" -ForegroundColor Cyan
Pause
