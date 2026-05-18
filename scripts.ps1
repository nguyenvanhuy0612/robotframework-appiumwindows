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

# Load .env (gitignored) so TWINE_USERNAME / TWINE_PASSWORD are available to twine.
# Falls back to ~/.pypirc if .env is absent.
if (Test-Path .env) {
    Write-Host "Loading credentials from .env..." -ForegroundColor Cyan
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#=][^=]*)=(.*)$') {
            Set-Item "env:$($matches[1].Trim())" $matches[2].Trim()
        }
    }
}

python -m twine upload dist/*