# One-Shot Demo — Single-Host Test Flow

This document describes the one-shot local demo flow (single host) used in this workspace.

What the one-shot command does
- Starts a local mock API (examples/mock_apis/users_api.py)
- Runs `acv validate` to generate tests and execute them against the mock API
- Produces human-readable and JSON drift reports in `output/`
- Generates AI remediation skills under `.acv/skills/` (e.g. `fix-validation-drift.md`)
- (Optional) Applies simple fixes and re-runs validation

Quick one-line (PowerShell) to run the whole flow locally:
```powershell
Start-Process -FilePath python -ArgumentList 'examples\mock_apis\users_api.py' -WindowStyle Hidden; Start-Sleep -s 2; .\.venv\Scripts\activate; acv validate examples/openapi/sample_users_api.yaml --api-url http://localhost:8000 --format all --output .\output; Start-Sleep -s 1; acv validate examples/openapi/sample_users_api.yaml --api-url http://localhost:8000 --format all --output .\output; notepad (Get-ChildItem .\output\drift_report_*.md | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
```

Notes about realism and remediation
- The mock API intentionally lacks full validation to demonstrate detection. We added a small validation patch to `examples/mock_apis/users_api.py` to demonstrate how remediations reduce issues.
- ACV will generate remediation guidance under `.acv/skills/`. Review `fix-validation-drift.md` before applying changes to production code.

Files produced by the flow
- Report: `output/drift_report_YYYYMMDD_HHMMSS.md`
- JSON: `output/drift_report_YYYYMMDD_HHMMSS.json`
- Remediation skills: `.acv/skills/fix-validation-drift.md`, `.acv/skills/apply-remediations.md`

If you want, I can also:
- Create a tiny script that runs the one-shot flow and optionally commits fixes, or
- Open `fix-validation-drift.md` and attempt to apply the suggested patches automatically (I will create diffs for review). 
