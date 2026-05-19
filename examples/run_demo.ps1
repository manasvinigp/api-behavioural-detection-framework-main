# PowerShell demo runner for Windows
# Run from repository root: .\examples\run_demo.ps1

param(
    [string]$Spec = "openapi/sample_users_api.yaml",
    [string]$Url = "http://localhost:8000",
    [string]$Output = "output/reports",
    [switch]$NoAI
)

# Create venv if missing
if (-not (Test-Path -Path ".venv" -PathType Container)) {
    python -m venv .venv
}

# Activate venv for current session
.\.venv\Scripts\Activate.ps1

# Install package editable
pip install -e .

# Start mock API in background
$proc = Start-Process -FilePath python -ArgumentList 'examples/mock_apis/users_api.py' -PassThru
Write-Host "Started mock API (PID=$($proc.Id)). Waiting 1s for server to start..."
Start-Sleep -Seconds 1

# Build validate command
$cmd = "acv validate --spec $Spec --api-url $Url --output $Output --format all"
if ($NoAI) { $cmd += " --no-ai-analysis" }

Write-Host "Running: $cmd"
Invoke-Expression $cmd

# Stop mock API
try {
    Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
    Write-Host "Mock API stopped."
} catch {
    Write-Host "Failed to stop mock API process"
}
