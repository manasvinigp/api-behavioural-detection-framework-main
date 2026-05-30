# Local CI demo script (PowerShell)
# Usage: From project root in PowerShell: .\demo\ci_run.ps1

.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
Start-Process -FilePath python -ArgumentList 'examples\mock_apis\users_api.py' -WindowStyle Hidden
Start-Sleep -s 2
acv validate examples/openapi/sample_users_api.yaml --api-url http://localhost:8000 --format all --output .\output
Get-ChildItem .\output\drift_report_*.md | Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object { notepad $_.FullName }
