# CI/CD Demo for ACV

This file describes how to run a CI-like demo locally and how the provided GitHub Actions workflow (`.github/workflows/acv_demo.yml`) works.

What the demo does
- Installs dependencies and the package
- Starts the included mock API
- Runs `acv validate` against the mock API
- Stores reports in `output/` and uploads them as artifacts in CI

Run locally (Linux / WSL / macOS)
```bash
# From project root
python -m venv .venv-ci
source .venv-ci/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
# Start mock API in background
python examples/mock_apis/users_api.py &
# Give server a moment
sleep 2
# Run ACV validate
acv validate examples/openapi/sample_users_api.yaml --api-url http://localhost:8000 --format all --output ./output
ls -l output/
```

Run locally (Windows PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
Start-Process -FilePath python -ArgumentList 'examples\mock_apis\users_api.py' -WindowStyle Hidden
Start-Sleep -s 2
acv validate examples/openapi/sample_users_api.yaml --api-url http://localhost:8000 --format all --output .\output
Get-ChildItem .\output\
```

Using the GitHub Actions workflow
- Trigger manually via the Actions tab (workflow name: `ACV Demo`) or with `workflow_dispatch` via API.
- The workflow uploads reports as artifacts named `acv-reports`.

CI Tips
- Use a dedicated test environment for `--api-url` when integrating with real services.
- Use `--fail-threshold` on the CLI to fail CI builds when drift exceeds policy. Example:
  `acv validate ... --fail-threshold 0.1`

Want me to add a CI badge and a small README section linking to this workflow?