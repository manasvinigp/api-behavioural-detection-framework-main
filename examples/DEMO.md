# Demo — Minimal commands

This project uses two simple commands for the full workflow. Keep it minimal:

- `acv init` — create `acv_config.yaml` in the current directory with sensible defaults.
- `acv validate` — run validation using `acv_config.yaml` (or pass a spec path). When config exists, `acv validate` will execute requests and produce reports.

Quick steps (Windows PowerShell):

```powershell
# Activate virtualenv (if you use one)
.\.venv\Scripts\Activate.ps1

# Generate configuration
acv init

# Run validation (autodiscovers acv_config.yaml)
acv validate
```

Or run against the sample spec directly:

```powershell
acv validate openapi/sample_users_api.yaml --api-url http://localhost:8000
```

Developer notes:
- Install dev dependencies and run tests:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
```

- The test suite passed locally (`183 passed`). If you encounter failures, ensure the virtualenv is activated and `acv init` has been run when using `acv validate` without arguments.

If you'd like, I can add a small GitHub Actions workflow that runs `acv init` and `acv validate` in CI.
