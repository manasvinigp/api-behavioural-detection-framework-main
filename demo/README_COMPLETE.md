# API Behavioral Drift Detection - Complete Demo Guide

This directory provides a **production-ready demonstration** of the API Behavioral Drift Detection Framework with step-by-step instructions for testing on real APIs including the Google Cloud Platform microservices demo.

## 🚀 Quick Start (2 Minutes)

```bash
# From project root
cd /Users/I764709/api-behavioural-detection-framework

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run automated demo
cd demo
python run_demo.py --target sample_demo

# View results
cat sample_demo/results/drift_report.md
```

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Demo Scenario 1: Mock API (Fastest)](#demo-scenario-1-mock-api-fastest)
- [Demo Scenario 2: Google Cloud Microservices](#demo-scenario-2-google-cloud-microservices)
- [Demo Scenario 3: Custom API](#demo-scenario-3-custom-api)
- [Understanding Results](#understanding-results)
- [Advanced Features](#advanced-features)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

**Required:**
- Python 3.9+ with pip
- Virtual environment (recommended)

```bash
# From project root
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

**Optional (for ML features):**
```bash
pip install sentence-transformers scipy scikit-learn
```

**Optional (for real microservices demo):**
- Docker Desktop
- Git

---

## Demo Scenario 1: Mock API (Fastest)

**Time: ~2 minutes | No external dependencies**

### Step 1: Run Demo

```bash
cd demo
python run_demo.py --mode mock --target sample_demo
```

### Step 2: View Results

```bash
# Human-readable report
cat sample_demo/results/drift_report.md

# JSON data
cat sample_demo/results/drift_report.json | python -m json.tool

# Root cause analysis
cat sample_demo/results/root_cause_analysis.json | python -m json.tool
```

### Step 3: Explore Output Structure

```bash
ls -R sample_demo/results/

# Expected structure:
# sample_demo/results/
# ├── drift_report.md
# ├── drift_report.json
# ├── test_results/
# ├── root_cause_analysis.json
# └── progressive_drift/drift_history.jsonl
```

### What This Tests

- ✅ Contract drift (missing fields, type mismatches)
- ✅ Validation drift (accepting invalid inputs)
- ✅ Behavioral drift (ML-based anomaly detection)
- ✅ Progressive drift (time-series trends)
- ✅ Root cause analysis with code examples

---

## Demo Scenario 2: Google Cloud Microservices

**Time: ~10 minutes | Requires Docker**

This demonstrates drift detection on a **real production-like microservices application**.

### Step 1: Clone and Start Microservices

```bash
# In a NEW terminal window
cd ~
git clone https://github.com/GoogleCloudPlatform/microservices-demo.git
cd microservices-demo

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Expected output:**
```
NAME                   SERVICE                STATUS
adservice              adservice              running (healthy)
cartservice            cartservice            running (healthy)
checkoutservice        checkoutservice        running (healthy)
currencyservice        currencyservice        running (healthy)
...
```

### Step 2: Wait for Services to Be Ready

```bash
# Wait 60 seconds for all services to initialize
sleep 60

# Test frontend is accessible
curl http://localhost:8080
```

### Step 3: Create OpenAPI Spec for Product Catalog Service

Since the microservices demo uses gRPC, we need to create an OpenAPI spec manually. Let's use a sample:

```bash
cd /Users/I764709/api-behavioural-detection-framework/demo

# Create specs directory
mkdir -p microservices_specs

# Create a sample OpenAPI spec for the product catalog service
cat > microservices_specs/productcatalog.yaml << 'EOF'
openapi: 3.0.0
info:
  title: Product Catalog Service
  version: 1.0.0
  description: Microservices demo - Product Catalog

servers:
  - url: http://localhost:3550

paths:
  /products:
    get:
      operationId: listProducts
      summary: List all products
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Product'

  /products/{id}:
    get:
      operationId: getProduct
      summary: Get product by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '404':
          description: Product not found

components:
  schemas:
    Product:
      type: object
      required:
        - id
        - name
        - price_usd
      properties:
        id:
          type: string
        name:
          type: string
        description:
          type: string
        picture:
          type: string
        price_usd:
          type: object
          properties:
            currency_code:
              type: string
            units:
              type: integer
            nanos:
              type: integer
        categories:
          type: array
          items:
            type: string
EOF
```

### Step 4: Run Drift Detection

```bash
# Test against Product Catalog Service
python run_demo.py \
  --mode real \
  --spec microservices_specs/productcatalog.yaml \
  --base-url http://localhost:3550 \
  --target microservices_demo/productcatalog
```

### Step 5: View Results

```bash
# View drift report
cat microservices_demo/productcatalog/results/drift_report.md

# Check drift score
cat microservices_demo/productcatalog/results/drift_report.json | jq '.overall_drift_score'

# View root causes
cat microservices_demo/productcatalog/results/root_cause_analysis.json | jq '.root_causes[] | {pattern, confidence, hypothesis}'
```

### Step 6: (Optional) Inject Drift to Test Detection

To see drift detection in action, modify a service:

```bash
# Go to microservices repo
cd ~/microservices-demo/src/productcatalogservice

# Make a backup
cp server.go server.go.bak

# Edit server.go to introduce drift:
# For example, comment out a required field in the Product struct
# Then rebuild:
docker-compose up -d --build productcatalogservice

# Re-run drift detection
cd /Users/I764709/api-behavioural-detection-framework/demo
python run_demo.py \
  --mode real \
  --spec microservices_specs/productcatalog.yaml \
  --base-url http://localhost:3550 \
  --target microservices_demo/productcatalog_drifted
```

### Step 7: Compare Results

```bash
# Compare drift scores
echo "Original drift score:"
cat microservices_demo/productcatalog/results/drift_report.json | jq '.overall_drift_score'

echo "After introducing drift:"
cat microservices_demo/productcatalog_drifted/results/drift_report.json | jq '.overall_drift_score'

# Diff the reports
diff microservices_demo/productcatalog/results/drift_report.md \
     microservices_demo/productcatalog_drifted/results/drift_report.md
```

### Step 8: Cleanup

```bash
cd ~/microservices-demo
docker-compose down
```

---

## Demo Scenario 3: Custom API

Test your own API:

```bash
cd demo

python run_demo.py \
  --mode real \
  --spec /path/to/your/openapi.yaml \
  --base-url https://your-api.example.com \
  --target custom_demo
```

---

## Understanding Results

### 1. Drift Report (drift_report.md)

**Sample Output:**

```markdown
# API Drift Detection Report
Generated: 2026-05-09 14:23:15 UTC

## Executive Summary
- Overall Drift Score: 0.42 (MODERATE)
- Total Issues: 12
  - Contract Drift: 5 issues (HIGH priority)
  - Validation Drift: 4 issues (MEDIUM priority)
  - Behavioral Drift: 3 issues (LOW priority)

## Critical Issues

### Issue #1: Missing Required Field 'email'
- **Endpoint:** POST /api/users
- **Severity:** HIGH
- **Type:** Contract Drift
- **Description:** Required field 'email' is missing from all tested responses

**Root Cause:**
The API implementation forgot to include the email field in the response serializer. The field is defined as required in the OpenAPI specification but is never returned.

**Suggested Fix:**
Add the email field to the UserResponse model:

```python
class UserResponse(BaseModel):
    id: int
    name: str
    email: str  # Add this field

@app.post("/users")
def create_user(user: UserInput) -> UserResponse:
    # Ensure email is included in response
    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email  # Include email
    )
```

**Estimated Effort:** Low
**Priority:** High
```

### 2. Root Cause Analysis (root_cause_analysis.json)

**Structure:**

```json
{
  "root_causes": [
    {
      "issue_id": "missing_required_field",
      "endpoint_id": "POST /api/users",
      "hypothesis": "Required field 'email' is missing from API response...",
      "contributing_factors": [
        "Serializer forgot to include field",
        "Database query missing projection"
      ],
      "confidence": "high",
      "evidence_references": ["test_001", "test_003", "test_007"]
    }
  ],
  "remediations": [
    {
      "title": "Fix Missing Required Field",
      "code_example": "...",
      "estimated_effort": "low",
      "priority": "high"
    }
  ],
  "systemic_issues": [
    "Multiple serializers missing required fields - consider automated testing"
  ]
}
```

### 3. Test Results (test_results/)

Individual drift detector outputs:

- `contract_drift.json` - Schema violations
- `validation_drift.json` - Validation issues
- `behavioral_drift.json` - ML-detected anomalies

### 4. Progressive Drift (progressive_drift/drift_history.jsonl)

Time-series data for trend analysis:

```json
{"timestamp": "2026-05-09T14:23:15Z", "contract_drift_score": 0.35, "validation_drift_score": 0.28}
{"timestamp": "2026-05-09T14:28:15Z", "contract_drift_score": 0.37, "validation_drift_score": 0.30}
```

---

## Advanced Features

### Enable ML-Based Detection

```bash
python run_demo.py \
  --mode mock \
  --enable-ml \
  --embedding-model all-MiniLM-L6-v2 \
  --target sample_demo
```

**Adds:**
- Response embedding similarity
- Distribution drift (KL/JS divergence)
- Anomaly detection (Isolation Forest)
- Behavioral clustering

### Enable AI Analysis (Claude)

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

python run_demo.py \
  --mode mock \
  --enable-ai \
  --target sample_demo
```

**Adds:**
- LLM-powered root cause analysis
- Natural language remediation suggestions
- Issue correlation detection

### Progressive Drift Tracking

Run the demo multiple times to build time-series data:

```bash
# Run every 5 minutes for an hour
for i in {1..12}; do
  echo "Run $i/12 at $(date)"
  python run_demo.py --mode mock --target sample_demo --append
  sleep 300
done

# Analyze trends
python analyze_drift_trend.py --input sample_demo/results/progressive_drift/drift_history.jsonl
```

**Output:**
- Change point detection
- Breach prediction
- Trend visualization

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: API Drift Detection
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e .
      
      - name: Run drift detection
        run: |
          cd demo
          python run_demo.py --mode mock --target ci_demo
      
      - name: Check drift threshold
        run: |
          drift_score=$(cat demo/ci_demo/results/drift_report.json | jq '.overall_drift_score')
          echo "Drift score: $drift_score"
          if (( $(echo "$drift_score > 0.3" | bc -l) )); then
            echo "::error::Drift score $drift_score exceeds threshold 0.3"
            exit 1
          fi
      
      - name: Upload drift report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: drift-report
          path: demo/ci_demo/results/
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('demo/ci_demo/results/drift_report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## API Drift Report\n\n' + report
            });
```

---

## Troubleshooting

### Error: "No module named 'api_contract_validator'"

**Solution:**
```bash
cd /Users/I764709/api-behavioural-detection-framework
pip install -e .
```

### Error: "Connection refused to localhost:8080"

**Solution:**
```bash
# Check Docker services
docker-compose ps

# Restart if needed
docker-compose down
docker-compose up -d

# Wait for services to be healthy
sleep 60
```

### Error: "ImportError: sentence_transformers"

**Solution:**
```bash
pip install sentence-transformers
```

### Error: "ANTHROPIC_API_KEY not found"

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or disable AI analysis
python run_demo.py --mode mock --no-ai --target sample_demo
```

### Error: "Docker not found"

**Solution:**
For Mock API demo, Docker is not required:
```bash
python run_demo.py --mode mock --target sample_demo
```

For real microservices demo, install Docker Desktop from https://www.docker.com/products/docker-desktop

---

## Next Steps

1. ✅ **Run the mock demo** to understand basic functionality
2. ✅ **Try the microservices demo** for real-world testing
3. ✅ **Test your own API** with custom specs
4. ✅ **Enable ML features** for advanced detection
5. ✅ **Set up progressive tracking** for continuous monitoring
6. ✅ **Integrate into CI/CD** to catch drift early

## Resources

- **Full Documentation:** `/docs/DETAILED_PROJECT_OVERVIEW.md`
- **Architecture Guide:** `/CLAUDE.md`
- **API Reference:** `/docs/api/`
- **Research Paper:** (Coming Q1 2026)
- **Issues/Support:** GitHub Issues

---

**Framework Version:** 0.2.0 | **Last Updated:** 2026-05-09 | **License:** MIT
