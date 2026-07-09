$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = "C:\Users\35160\AppData\Local\Programs\Python\Python312\python.exe"
$pyinstaller = Join-Path (Split-Path $python) "Scripts\pyinstaller.exe"
$iscc = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $candidate = "C:\Users\35160\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
    if (Test-Path $candidate) {
        $iscc = $candidate
    }
}

if (-not (Test-Path $python)) {
    throw "Python not found at $python"
}
if (-not (Test-Path $pyinstaller)) {
    throw "PyInstaller not found at $pyinstaller"
}
if (-not $iscc) {
    throw "ISCC.exe not found. Install Inno Setup 6 first."
}

$usedDrives = (Get-PSDrive -PSProvider FileSystem).Name
$driveLetter = @("X", "Y", "Z", "W", "V", "U", "T", "S", "R", "Q") | Where-Object { $usedDrives -notcontains $_ } | Select-Object -First 1
if (-not $driveLetter) {
    throw "No free drive letter found for temporary subst mapping."
}

$substDrive = "${driveLetter}:"
$workspaceRoot = "$substDrive\"
$substCreated = $false

try {
    cmd /c "subst $substDrive `"$root`"" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create temporary drive mapping $substDrive for $root"
    }
    $substCreated = $true

    $frontendDist = Join-Path $workspaceRoot "frontend\dist"
    if (-not (Test-Path $frontendDist)) {
        throw "Frontend dist not found at $frontendDist"
    }

    $cacheRoot = Join-Path $env:LOCALAPPDATA "datalab\datalab\Cache\models"
    if (-not (Test-Path $cacheRoot)) {
        throw "Surya model cache not found at $cacheRoot"
    }

    $buildRoot = Join-Path $workspaceRoot "build\zclum-prism-ocr"
    $distRoot = Join-Path $workspaceRoot "dist"
    $installerRoot = Join-Path $env:TEMP ("zclum-prism-ocr-installer-" + [guid]::NewGuid().ToString("N"))
    $modelStage = Join-Path $installerRoot "models"
    $installerOutput = Join-Path $installerRoot "output"

    Remove-Item $buildRoot, $distRoot, $installerRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $buildRoot, $distRoot, $installerRoot, $modelStage, $installerOutput | Out-Null

    Write-Host "Copying Surya model cache to staging..."
    Copy-Item -Path (Join-Path $cacheRoot "*") -Destination $modelStage -Recurse -Force

    Write-Host "Building onedir bundle..."
    & $pyinstaller `
        --noconfirm `
        --clean `
        --onedir `
        --windowed `
        --name "ZCLUM Prism OCR" `
        --distpath $distRoot `
        --workpath $buildRoot `
        --specpath $buildRoot `
        --add-data "$frontendDist;frontend\dist" `
        --collect-all docling `
        --collect-all marker `
        --collect-all magic_pdf `
        --collect-all nougat `
        --collect-all paddlex `
        --collect-all paddleocr `
        --collect-all surya `
        --collect-submodules surya `
        --collect-submodules transformers `
        --collect-submodules uvicorn `
        --collect-submodules fastapi `
        --collect-submodules pydantic `
        --collect-submodules pypdfium2 `
        "$workspaceRoot\desktop_launcher.py"

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE"
    }

    $appDist = Join-Path $distRoot "ZCLUM Prism OCR"
    if (-not (Test-Path $appDist)) {
        throw "Expected app directory not found at $appDist"
    }

    Write-Host "Pruning package license directories to avoid long install paths..."
    Get-ChildItem -Path (Join-Path $appDist "_internal") -Recurse -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '\\\.dist-info\\licenses($|\\)' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "Compiling installer..."
    & $iscc `
        /DAppSource="$appDist" `
        /DModelSource="$modelStage" `
        /DInstallerOutput="$installerOutput" `
        "$workspaceRoot\packaging\Lumia-ScriptorRAG.iss"

    if ($LASTEXITCODE -ne 0) {
        throw "Installer build failed with exit code $LASTEXITCODE"
    }

    Write-Host "Build complete."
    Write-Host "App: $appDist"
    Write-Host "Installer: $installerOutput"
}
finally {
    if ($substCreated) {
        cmd /c "subst /d $substDrive" | Out-Null
    }
}
