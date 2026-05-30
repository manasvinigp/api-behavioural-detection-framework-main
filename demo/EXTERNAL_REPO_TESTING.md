# Testing ACV Against an External REST API Repository

This guide shows minimal steps to run the API Contract Validator (`acv`) against an external repository that exposes REST APIs.

**Prerequisites**
- Python 3.10+ and a virtual environment with the project installed (`pip install -e .`).
- `acv` CLI available in your PATH (virtualenv activated).
- An OpenAPI spec for the target API. If the repo doesn't provide one, create one (see Notes).

**Quick one-shot (PowerShell)**
```powershell
# From your ACV project root
.\.venv\Scripts\Activate.ps1
# If you don't have a config, create a simple one
acv init --spec path\to\your_openapi.yaml --api-url http://TARGET_HOST:PORT --yes
# Run validation against the target API
acv validate path\to\your_openapi.yaml --api-url http://TARGET_HOST:PORT --format all --output .\external_output
# View report
notepad .\external_output\drift_report_*.md
```

**Recommended steps (more explicit)**
1. Clone or update the external repo and start its API services (Docker or native):
```bash
git clone https://example.com/your-api-repo.git
cd your-api-repo
# if docker-compose is provided
docker-compose up -d
# or run the server per repo instructions
```

2. Obtain or create an OpenAPI spec:
- If the repo includes `openapi.yaml` or `swagger.json`, use it.
- If not, generate one using tools (Swagger Editor, `flask-swagger`, `drf-yasg`), or hand-write a minimal spec containing the endpoints you want tested.

3. From the ACV project root run:
```bash
# Activate venv first
.\.venv\Scripts\activate
# Validate
acv validate path/to/external/openapi.yaml --api-url http://localhost:PORT --format all --output ./external_output
```

4. Review outputs:
- Human report: `external_output/drift_report_*.md`
- JSON: `external_output/drift_report_*.json`
- AI remediation skills (if generated): `.acv/skills/fix-validation-drift.md` or `.acv/skills/apply-remediations.md`

5. Apply remediations:
- Manual: open the remediation skill and apply fixes in the external repo per instructions.
- Interactive (semi-automatic): Use the `.acv/skills/apply-remediations.md` workflow to apply code patches (review diffs before committing).

**Notes & Tips**
- If the external API is behind auth, add required headers in `acv_config.yaml` under `api.headers` or pass via environment.
- For multi-service repos, run ACV against each service's OpenAPI spec and base URL.
- Use `acv generate_tests` to preview the test distribution before executing:
```
acv generate_tests path/to/openapi.yaml --max-tests 50
```

**CI integration**
- Add `acv validate` as a CI job that runs against a deployed test environment (staging). Fail the job when `--fail-threshold` is exceeded:
```yaml
script:
  - .venv\Scripts\activate
  - acv validate path/to/openapi.yaml --api-url $STAGING_API_URL --format json --output ./ci_output --fail-threshold 0.1
```

**If you need help creating an OpenAPI spec from the repo, tell me which framework the repo uses (Flask/FastAPI/Django/Express/etc.) and I can provide targeted commands.**
