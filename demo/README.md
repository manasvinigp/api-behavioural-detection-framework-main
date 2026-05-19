# Demo: API Behavioral Drift Detection Framework

This demo shows a minimal, local example of running the framework against the included sample API.

Prerequisites
- Python 3.10+ virtual environment (the repository includes a `.venv` if you used the project setup)
- The package installed in editable mode: `pip install -e .`

Quick steps (Windows)

1. Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
# or
.\.venv\Scripts\activate
```

2. Install the project (if not already installed):

```powershell
pip install -e .
```

3. Start the sample/mock API (runs locally on port 8000):

```powershell
python mock_apis/users_api.py
```

4. Run the validator against the included OpenAPI spec:

```powershell
acv validate --spec openapi/sample_users_api.yaml --url http://localhost:8000
```

What this demo does
- Parses the OpenAPI spec in `openapi/sample_users_api.yaml`
- Generates a small suite of tests (valid/invalid/boundary)
- Executes them against the running mock API
- Prints a drift summary to the console and writes reports to the configured output folder

Programmatic example

You can also call the library from Python:

```python
from pathlib import Path
from api_contract_validator.input.openapi.parser import OpenAPIParser
from api_contract_validator.schema.contract.builder import ContractBuilder
from api_contract_validator.generation.test_generator import MasterTestGenerator
from api_contract_validator.execution.runner.executor import TestExecutor
from api_contract_validator.analysis.drift.detector import MultiDimensionalDriftDetector

spec = OpenAPIParser().parse_file(Path('openapi/sample_users_api.yaml'))
contract = ContractBuilder().merge(spec, {})
tests = MasterTestGenerator().generate(contract)
results = TestExecutor('http://localhost:8000').execute_parallel(tests)
report = MultiDimensionalDriftDetector(contract).analyze(results)
print(report)
```

Notes
- This demo is intentionally minimal and meant for local exploration. For reproducible evaluation or CI, follow the instructions in the project `README.md`.