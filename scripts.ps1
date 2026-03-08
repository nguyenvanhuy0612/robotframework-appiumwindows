# PowerShell script to clean, build, and publish the package

# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Cyan
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
Get-ChildItem -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force

# Build the package
Write-Host "Building the package..." -ForegroundColor Cyan
python -m build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Check the distribution
Write-Host "Checking the distribution..." -ForegroundColor Cyan
python -m twine check dist/*

if ($LASTEXITCODE -ne 0) {
    Write-Host "Twine check failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Optional: Publish to PyPI
$choice = Read-Host "Do you want to publish to PyPI now? (y/n)"
if ($choice -eq 'y') {
    Write-Host "Publishing to PyPI..." -ForegroundColor Cyan
    python -m twine upload dist/*
} else {
    Write-Host "Skipping upload." -ForegroundColor Yellow
}
