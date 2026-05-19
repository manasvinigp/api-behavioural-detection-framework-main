# Contributing

Thank you for contributing. Quick guidelines:

- Run tests before submitting PRs:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
```

- Coding style: run `black` and `ruff` before committing.
- Write unit tests for new features and update `docs/DETAILED_PROJECT_OVERVIEW.md` when APIs change.
- For large changes, open an issue first to discuss design.

Maintainers will review PRs and request changes as needed.
