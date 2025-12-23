# ============================================================================
# AEPython Release Package Builder
# ============================================================================

Write-Host "=== AEPython Release Package Builder ===" -ForegroundColor Cyan
Write-Host ""

# Get version number
$version = Read-Host "Enter version number (e.g., 1.0.0)"
if (-not $version.StartsWith("v")) {
    $versionTag = "v$version"
} else {
    $versionTag = $version
    $version = $version.TrimStart("v")
}

Write-Host ""
Write-Host "Building AEPython $versionTag..." -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# Path Setup (all relative to script location)
# ============================================================================

$SCRIPT_ROOT = $PSScriptRoot
$AEGP_DIR = Join-Path $SCRIPT_ROOT "AEGP"
$RELEASE_DIR = Join-Path $SCRIPT_ROOT "Release_$versionTag"  # No spaces!
$ZIP_NAME = "AEPython-$versionTag.zip"
$ZIP_PATH = Join-Path $RELEASE_DIR $ZIP_NAME

# Python download info
$PYTHON_VERSION = "3.14.2"
$PYTHON_ZIP = Join-Path $SCRIPT_ROOT "python-$PYTHON_VERSION-embed-amd64.zip"
$GETPIP_PY = Join-Path $SCRIPT_ROOT "get-pip.py"
$PYTHON_FOLDER = "python-$PYTHON_VERSION-embed-amd64"
$PYTHON_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-embed-amd64.zip"

# AEGP internal structure
$AEGP_AEPYTHON = Join-Path $AEGP_DIR "AEPython"
$AEGP_AE = Join-Path $AEGP_AEPYTHON "AE"
$AEGP_PLUGINS = Join-Path $AEGP_AE "Plug-ins\AEPython"
$AEGP_SCRIPTS = Join-Path $AEGP_AE "Scripts"
$AEGP_USER_DOCS = Join-Path $AEGP_AEPYTHON "User Documents"
$PYTHON_ROOT = Join-Path $AEGP_PLUGINS $PYTHON_FOLDER
$PYTHON_EXE = Join-Path $PYTHON_ROOT "python.exe"
$PTH = Join-Path $PYTHON_ROOT "python314._pth"

# Source paths (relative to script root)
$SOURCE_PLUGIN_DIR = Join-Path $SCRIPT_ROOT "Plug-ins AE\AEPython"
$SOURCE_COMPILED_DIR = Join-Path $SCRIPT_ROOT "Win\x64\Release\AEPython"
$SOURCE_SCRIPTS_DIR = Join-Path $SCRIPT_ROOT "Scripts AE"
$REQUIREMENTS_TXT = Join-Path $SCRIPT_ROOT "requirements.txt"

# ============================================================================
# Clean and Create AEGP Directory Structure
# ============================================================================

Write-Host "[1/10] Creating AEGP directory structure..." -ForegroundColor Cyan

# Clean AEGP if it exists
if (Test-Path $AEGP_DIR) {
    Remove-Item -Recurse -Force $AEGP_DIR
}

# Create directory structure
New-Item -ItemType Directory -Path $AEGP_PLUGINS -Force
New-Item -ItemType Directory -Path $AEGP_SCRIPTS -Force
New-Item -ItemType Directory -Path $AEGP_USER_DOCS -Force

Write-Host "  ✓ AEGP structure created" -ForegroundColor Green

# ============================================================================
# Download Python Embeddable
# ============================================================================

Write-Host ""
Write-Host "[2/10] Downloading Python $PYTHON_VERSION embeddable..." -ForegroundColor Cyan

if (!(Test-Path $PYTHON_ZIP)) {
    try {
        Invoke-WebRequest -Uri $PYTHON_URL -OutFile $PYTHON_ZIP
        Write-Host "  ✓ Python downloaded" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to download Python: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✓ Python already downloaded (using cached)" -ForegroundColor Green
}

# ============================================================================
# Download get-pip.py
# ============================================================================

Write-Host ""
Write-Host "[3/10] Downloading get-pip.py..." -ForegroundColor Cyan

if (!(Test-Path $GETPIP_PY)) {
    try {
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GETPIP_PY
        Write-Host "  ✓ get-pip.py downloaded" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to download get-pip.py: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✓ get-pip.py already downloaded (using cached)" -ForegroundColor Green
}

# ============================================================================
# Extract Python to AEGP
# ============================================================================

Write-Host ""
Write-Host "[4/10] Extracting Python to AEGP..." -ForegroundColor Cyan

if (!(Test-Path $PYTHON_ROOT)) {
    Expand-Archive -Path $PYTHON_ZIP -DestinationPath $PYTHON_ROOT -Force
    Write-Host "  ✓ Python extracted to AEGP" -ForegroundColor Green
} else {
    Write-Host "  ✓ Python already extracted" -ForegroundColor Green
}

# ============================================================================
# Configure Python and Install pip
# ============================================================================

Write-Host ""
Write-Host "[5/10] Configuring Python and installing pip..." -ForegroundColor Cyan

Push-Location $PYTHON_ROOT

# Update PTH for full site-packages access
(Get-Content -Path $PTH) -replace "#import site", "import site" | Set-Content -Path $PTH
Write-Host "  ✓ PTH file updated" -ForegroundColor Green

# Install pip
& $PYTHON_EXE $GETPIP_PY
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ pip installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to install pip" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# ============================================================================
# Install Python Requirements
# ============================================================================

Write-Host ""
Write-Host "[6/10] Installing Python requirements..." -ForegroundColor Cyan

if (Test-Path $REQUIREMENTS_TXT) {
    Push-Location $PYTHON_ROOT
    & $PYTHON_EXE -m pip install -r $REQUIREMENTS_TXT --upgrade
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Requirements installed (PySide6, etc.)" -ForegroundColor Green
    } else {
        Write-Host "  ! Warning: Some requirements may have failed to install" -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host "  ! Warning: requirements.txt not found at: $REQUIREMENTS_TXT" -ForegroundColor Yellow
}

# ============================================================================
# Copy Plugin Files
# ============================================================================

Write-Host ""
Write-Host "[7/10] Copying plugin files to AEGP..." -ForegroundColor Cyan

if (Test-Path $SOURCE_PLUGIN_DIR) {
    Get-ChildItem -Path $SOURCE_PLUGIN_DIR | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $AEGP_PLUGINS -Recurse -Force
    }
    Write-Host "  ✓ Plugin files copied from: Plug-ins AE\AEPython" -ForegroundColor Green
} else {
    Write-Host "  ! Warning: Plugin source directory not found: $SOURCE_PLUGIN_DIR" -ForegroundColor Yellow
}

# ============================================================================
# Copy Compiled Files
# ============================================================================

Write-Host ""
Write-Host "[8/10] Copying compiled plugin files to AEGP..." -ForegroundColor Cyan

if (Test-Path $SOURCE_COMPILED_DIR) {
    Get-ChildItem -Path $SOURCE_COMPILED_DIR | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $AEGP_PLUGINS -Recurse -Force
    }
    Write-Host "  ✓ Compiled files copied from: Win\x64\Release\AEPython" -ForegroundColor Green
} else {
    Write-Host "  ! Warning: Compiled files directory not found: $SOURCE_COMPILED_DIR" -ForegroundColor Yellow
}

# ============================================================================
# Copy Scripts
# ============================================================================

Write-Host ""
Write-Host "[9/10] Copying AE scripts to AEGP..." -ForegroundColor Cyan

if (Test-Path $SOURCE_SCRIPTS_DIR) {
    Get-ChildItem -Path $SOURCE_SCRIPTS_DIR | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $AEGP_SCRIPTS -Recurse -Force
    }
    Write-Host "  ✓ Scripts copied from: Scripts AE" -ForegroundColor Green
} else {
    Write-Host "  ! Warning: Scripts directory not found: $SOURCE_SCRIPTS_DIR" -ForegroundColor Yellow
}

# ============================================================================
# Copy User Files
# ============================================================================

Write-Host ""
Write-Host "[10/10] Copying User Files to AEGP..." -ForegroundColor Cyan

$SOURCE_USER_FILES = Join-Path $SCRIPT_ROOT "User Files"

if (Test-Path $SOURCE_USER_FILES) {
    Get-ChildItem -Path $SOURCE_USER_FILES | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $AEGP_USER_DOCS -Recurse -Force
    }
    Write-Host "  ✓ User Files copied to User Documents" -ForegroundColor Green
} else {
    Write-Host "  ! Warning: User Files directory not found: $SOURCE_USER_FILES" -ForegroundColor Yellow
}

# ============================================================================
# Create Release Directory and Zip
# ============================================================================

Write-Host ""
Write-Host "Creating release package..." -ForegroundColor Cyan

# Create release directory
if (!(Test-Path $RELEASE_DIR)) {
    New-Item -ItemType Directory -Path $RELEASE_DIR
}

# Remove old zip if exists
if (Test-Path $ZIP_PATH) {
    Remove-Item $ZIP_PATH -Force
}

# Create zip from AEGP directory contents
Compress-Archive -Path "$AEGP_DIR\*" -DestinationPath $ZIP_PATH -CompressionLevel Optimal

Write-Host "  ✓ Release package created" -ForegroundColor Green

# ============================================================================
# Summary
# ============================================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "✅ Release Package Build Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Package Info:" -ForegroundColor Yellow
Write-Host "  Version:      $versionTag" -ForegroundColor White
Write-Host "  Location:     $RELEASE_DIR" -ForegroundColor White
Write-Host "  Filename:     $ZIP_NAME" -ForegroundColor White

if (Test-Path $ZIP_PATH) {
    Write-Host "  Size:         $([math]::Round((Get-Item $ZIP_PATH).Length / 1MB, 2)) MB" -ForegroundColor White
}

Write-Host ""
Write-Host "AEGP Build Structure:" -ForegroundColor Yellow
Write-Host "  AEGP/" -ForegroundColor White
Write-Host "  └── AEPython/" -ForegroundColor White
Write-Host "      ├── AE/" -ForegroundColor White
Write-Host "      │   ├── Plug-ins/AEPython/" -ForegroundColor White
Write-Host "      │   │   ├── python-$PYTHON_VERSION-embed-amd64/" -ForegroundColor White
Write-Host "      │   │   │   └── [pip + packages installed]" -ForegroundColor White
Write-Host "      │   │   ├── [plugin source files]" -ForegroundColor White
Write-Host "      │   │   └── [compiled binaries]" -ForegroundColor White
Write-Host "      │   └── Scripts/" -ForegroundColor White
Write-Host "      │       └── [AE scripts]" -ForegroundColor White
Write-Host "      └── User Documents/" -ForegroundColor White
Write-Host ""
Write-Host "Zip Package Contains:" -ForegroundColor Yellow
Write-Host "  All contents of AEGP folder ready for distribution" -ForegroundColor White
Write-Host ""

# Ask if user wants to open the folder
$open = Read-Host "Open release folder? (y/n)"
if ($open -eq "y") {
    Start-Process explorer $RELEASE_DIR
}


# ============================================================================
# GitHub Release
# ============================================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
$createRelease = Read-Host "Create GitHub release now? (y/n)"

if ($createRelease -eq "y") {
    Write-Host ""
    Write-Host "Creating GitHub release..." -ForegroundColor Cyan
    
    # Get release notes
    Write-Host ""
    Write-Host "Enter release notes (press Enter twice when done):" -ForegroundColor Yellow
    $releaseNotes = ""
    $lineCount = 0
    do {
        $line = Read-Host
        if ($line) {
            $releaseNotes += "$line`n"
            $lineCount = 0
        } else {
            $lineCount++
        }
    } while ($lineCount -lt 1)
    
    # Default notes if empty
    if (-not $releaseNotes.Trim()) {
        $releaseNotes = @"
## AEPython $versionTag

New release of AEPython - Python integration for After Effects.

### Installation
Download AEPython-$versionTag.zip and follow the installation instructions.

### Note
The automatic "Source code" archives contain the full Adobe-Python-Bridge repository.
For the AEPython plugin installer, download AEPython-$versionTag.zip above.
"@
    }
    
    Write-Host "Creating GitHub release..." -ForegroundColor Cyan
    
    # Navigate to repo root for git commands
    $repoRoot = Join-Path $SCRIPT_ROOT ".."
    Set-Location $repoRoot
    
    # Create release using GitHub CLI - only upload the plugin zip
    gh release create $versionTag `
        --title "AEPython $versionTag" `
        --notes $releaseNotes `
        $ZIP_PATH
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ GitHub release created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Uploaded files:" -ForegroundColor Yellow
        Write-Host "  - AEPython-$versionTag.zip (plugin installer)" -ForegroundColor White
        Write-Host "  - Source code archives (auto-generated by GitHub)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "View your release at:" -ForegroundColor Cyan
        Write-Host "  https://github.com/GuyMicciche/Adobe-Python-Bridge/releases/tag/$versionTag" -ForegroundColor Blue
    } else {
        Write-Host ""
        Write-Host "✗ GitHub release creation failed!" -ForegroundColor Red
        Write-Host "You can manually upload $ZIP_NAME from $RELEASE_DIR" -ForegroundColor Yellow
    }
    
    # Return to AEPython directory
    Set-Location $SCRIPT_ROOT
} else {
    Write-Host ""
    Write-Host "Skipping GitHub release." -ForegroundColor Yellow
    Write-Host "You can manually upload $ZIP_NAME later." -ForegroundColor White
}

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green

Pause