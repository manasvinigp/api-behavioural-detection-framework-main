# One-shot PRD Input Test — Demo

This document shows a minimal one-shot demo that runs the API Behavioral Validator using a PRD file as an additional input source. It uses the `shoppingassistant_prd.md` PRD in the same demo folder and the existing OpenAPI spec.

Prerequisites

- Python virtual environment activated for the repo (see project README)
- Local demo service running (the demo service serves the `/shoppingassistant` endpoint on port 8080)
- `acv` CLI available (the project entrypoint is `api_contract_validator.cli.main`)

Steps

1. Start the demo service (example using the included demo runner):

```powershell
# from repository root
python demo/run_demo.py --port 8080
```

2. Run a one-shot validation that supplies both the OpenAPI spec and the PRD file. This will generate a report under `output/` and may also write to `demo/test_demo/reports/` depending on your config.

```powershell
# from repository root
python -m api_contract_validator.cli.main validate demo/test_demo/openapi/shoppingassistant.yaml --api-url http://127.0.0.1:8080 --prd demo/test_demo/prd/shoppingassistant_prd.md
```

3. Inspect the generated report (example location):

- `output/drift_report_<timestamp>.json`
- `output/drift_report_<timestamp>.md`

Quick curl examples

```bash
curl -X POST http://127.0.0.1:8080/shoppingassistant -H "Content-Type: application/json" -d '{"message":"Recommend casual shoes"}'

curl -X POST http://127.0.0.1:8080/shoppingassistant -H "Content-Type: application/json" -d '{"image":"https://example.com/shoe.jpg"}'
```

Expected outcomes

- The validator uses the PRD to supplement the OpenAPI spec: missing/nullable fields and business rules from the PRD will be scored and used to generate validation and behavioral tests.
- Invalid inputs (e.g., missing `message`) should be flagged as validation drift if the service accepts them.

Troubleshooting

- If the demo service path differs, update the OpenAPI spec at `demo/test_demo/openapi/shoppingassistant.yaml` to match the running service.
- If you see schema-related false positives, ensure `received` fields are present (use explicit `null` when absent) as required by the PRD.

Next steps

- Automate this command in CI to run PRD-driven validation on each deployment.
- Use the PRD as input for intelligent test generation to create adversarial and boundary cases.
