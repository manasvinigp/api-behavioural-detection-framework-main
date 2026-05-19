#!/usr/bin/env python3
"""
Standalone Demo - API Behavioral Drift Detection Framework
Runs without package installation for immediate testing
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def create_demo_directories(base_path: Path):
    """Create directory structure for demo results."""
    (base_path / "results").mkdir(parents=True, exist_ok=True)
    (base_path / "results" / "test_results").mkdir(exist_ok=True)
    (base_path / "results" / "progressive_drift").mkdir(exist_ok=True)
    (base_path / "config").mkdir(exist_ok=True)
    (base_path / "logs").mkdir(exist_ok=True)
    print(f"✅ Created demo directory structure at: {base_path}")

def create_sample_openapi_spec():
    """Create sample OpenAPI spec for demo."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Demo User API",
            "version": "1.0.0",
            "description": "Sample API for drift detection demo"
        },
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "summary": "List all users",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create a new user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserInput"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "400": {"description": "Bad Request"}
                    }
                }
            },
            "/users/{userId}": {
                "get": {
                    "operationId": "getUserById",
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "minimum": 1}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "404": {"description": "Not Found"}
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["id", "email", "name"],
                    "properties": {
                        "id": {"type": "integer", "minimum": 1},
                        "email": {"type": "string", "format": "email"},
                        "name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150},
                        "status": {"type": "string", "enum": ["active", "inactive"]}
                    }
                },
                "UserInput": {
                    "type": "object",
                    "required": ["email", "name"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150}
                    }
                }
            }
        }
    }

def generate_simulated_drift_issues():
    """Generate simulated drift detection results."""
    return {
        "contract_drift": {
            "violations": [
                {
                    "endpoint": "POST /users",
                    "issue": "Missing required field 'email' in response",
                    "severity": "HIGH",
                    "test_cases_affected": 5,
                    "confidence": 0.95
                },
                {
                    "endpoint": "GET /users/{userId}",
                    "issue": "Unexpected field 'internal_id' found in response",
                    "severity": "MEDIUM",
                    "test_cases_affected": 3,
                    "confidence": 0.88
                },
                {
                    "endpoint": "POST /users",
                    "issue": "Type mismatch: field 'age' expected integer, got string",
                    "severity": "HIGH",
                    "test_cases_affected": 4,
                    "confidence": 0.92
                }
            ],
            "score": 0.35
        },
        "validation_drift": {
            "violations": [
                {
                    "endpoint": "POST /users",
                    "issue": "Accepts invalid email format 'not-an-email'",
                    "severity": "MEDIUM",
                    "test_cases_affected": 3,
                    "confidence": 0.90
                },
                {
                    "endpoint": "POST /users",
                    "issue": "Accepts negative age value (-5)",
                    "severity": "MEDIUM",
                    "test_cases_affected": 2,
                    "confidence": 0.85
                },
                {
                    "endpoint": "POST /users",
                    "issue": "Accepts name exceeding max length (150 chars when max is 100)",
                    "severity": "LOW",
                    "test_cases_affected": 2,
                    "confidence": 0.80
                }
            ],
            "score": 0.28
        },
        "behavioral_drift": {
            "anomalies": [
                {
                    "endpoint": "GET /users/{userId}",
                    "issue": "Response embedding similarity below threshold (0.62)",
                    "severity": "LOW",
                    "test_cases_affected": 2,
                    "confidence": 0.75
                },
                {
                    "endpoint": "GET /users",
                    "issue": "Distribution shift detected (JS divergence: 0.23)",
                    "severity": "LOW",
                    "test_cases_affected": 4,
                    "confidence": 0.70
                }
            ],
            "score": 0.15
        },
        "overall_drift_score": 0.42,
        "total_tests_executed": 25,
        "tests_passed": 15,
        "tests_failed": 10,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_root_cause_analysis():
    """Generate root cause analysis with code examples."""
    return {
        "root_causes": [
            {
                "pattern": "missing_required_field",
                "endpoint": "POST /users",
                "confidence": "high",
                "hypothesis": "Required field 'email' is missing from API response. The field is defined in the specification but never returned by the implementation.",
                "why": "The API implementation likely forgot to include the field in the response serializer or database query projection.",
                "evidence": [
                    "Test case test_001: email field absent",
                    "Test case test_003: email field absent",
                    "Test case test_007: email field absent"
                ],
                "remediation": {
                    "title": "Add missing email field to response",
                    "description": "Include the email field in the UserResponse serializer",
                    "code_example": """# Fix for missing email field

class UserResponse(BaseModel):
    id: int
    name: str
    email: str  # ← Add this required field
    age: Optional[int] = None
    status: str = "active"

@app.post("/users")
def create_user(user: UserInput) -> UserResponse:
    new_user = db.create_user(user)
    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,  # ← Make sure to include it
        age=new_user.age,
        status=new_user.status
    )""",
                    "estimated_effort": "low",
                    "priority": "high",
                    "steps": [
                        "1. Open the user serializer/response model file",
                        "2. Add 'email: str' field to the response schema",
                        "3. Update the endpoint handler to include email in the response",
                        "4. Run tests to verify the fix",
                        "5. Update OpenAPI spec if needed"
                    ]
                }
            },
            {
                "pattern": "type_mismatch",
                "endpoint": "POST /users",
                "confidence": "high",
                "hypothesis": "Field 'age' has type mismatch. Expected integer but got string.",
                "why": "Type coercion issue in serializer, database schema returns string, or incorrect type casting in business logic.",
                "evidence": [
                    "Test case test_004: age='25' (string) instead of 25 (int)",
                    "Test case test_005: age='30' (string) instead of 30 (int)"
                ],
                "remediation": {
                    "title": "Fix type conversion for age field",
                    "description": "Ensure age field is properly typed as integer in serializer",
                    "code_example": """# Fix for type mismatch

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int  # ← Ensure correct type annotation

    class Config:
        # Enable strict type validation
        validate_assignment = True

@app.post("/users")
def create_user(user: UserInput) -> UserResponse:
    new_user = db.create_user(user)
    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        age=int(new_user.age)  # ← Explicit type conversion
    )""",
                    "estimated_effort": "low",
                    "priority": "high"
                }
            },
            {
                "pattern": "missing_input_validation",
                "endpoint": "POST /users",
                "confidence": "medium",
                "hypothesis": "Endpoint accepts invalid input that should be rejected. Missing validation for email format and age constraints.",
                "why": "Validation middleware not applied, or validator configuration incomplete.",
                "evidence": [
                    "Test case test_invalid_001: Accepted invalid email 'not-an-email'",
                    "Test case test_invalid_002: Accepted negative age -5"
                ],
                "remediation": {
                    "title": "Add input validation",
                    "description": "Add Pydantic validators for email and age fields",
                    "code_example": """# Add validation

from pydantic import BaseModel, Field, validator, EmailStr

class UserInput(BaseModel):
    email: EmailStr  # ← Use EmailStr for automatic validation
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)  # ← ge/le for constraints

    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v

    @validator('email')
    def validate_email_domain(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v""",
                    "estimated_effort": "medium",
                    "priority": "medium"
                }
            }
        ],
        "summary": {
            "total_patterns_found": 3,
            "high_confidence": 2,
            "medium_confidence": 1,
            "low_confidence": 0,
            "systemic_issues": [
                "Multiple serializers missing required fields - consider implementing automated schema validation tests",
                "Input validation gaps across POST endpoints - recommend adding a validation middleware layer"
            ],
            "quick_wins": [
                "Add email field to UserResponse (5 minutes, fixes 3 test failures)",
                "Fix age type conversion (10 minutes, fixes 2 test failures)"
            ]
        }
    }

def create_markdown_report(drift_data, root_causes):
    """Generate human-readable markdown report."""
    report = f"""# API Behavioral Drift Detection Report

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
**API:** Demo User API v1.0.0
**Base URL:** http://localhost:8000

---

## 📊 Executive Summary

- **Overall Drift Score:** {drift_data['overall_drift_score']:.2f} (MODERATE)
- **Total Issues Found:** {len(drift_data['contract_drift']['violations']) + len(drift_data['validation_drift']['violations']) + len(drift_data['behavioral_drift']['anomalies'])}
- **Tests Executed:** {drift_data['total_tests_executed']}
- **Tests Passed:** {drift_data['tests_passed']} ({drift_data['tests_passed']/drift_data['total_tests_executed']*100:.1f}%)
- **Tests Failed:** {drift_data['tests_failed']} ({drift_data['tests_failed']/drift_data['total_tests_executed']*100:.1f}%)

### Drift Breakdown

| Type | Score | Issues | Severity |
|------|-------|--------|----------|
| Contract Drift | {drift_data['contract_drift']['score']:.2f} | {len(drift_data['contract_drift']['violations'])} | 🔴 HIGH |
| Validation Drift | {drift_data['validation_drift']['score']:.2f} | {len(drift_data['validation_drift']['violations'])} | 🟡 MEDIUM |
| Behavioral Drift | {drift_data['behavioral_drift']['score']:.2f} | {len(drift_data['behavioral_drift']['anomalies'])} | 🟢 LOW |

---

## 🔥 Critical Issues

"""

    # Add contract drift issues
    report += "### Contract Drift Issues\n\n"
    for i, issue in enumerate(drift_data['contract_drift']['violations'], 1):
        report += f"""#### Issue #{i}: {issue['issue']}

- **Endpoint:** `{issue['endpoint']}`
- **Severity:** {issue['severity']}
- **Tests Affected:** {issue['test_cases_affected']}
- **Confidence:** {issue['confidence']:.0%}

"""

    # Add validation drift issues
    report += "\n### Validation Drift Issues\n\n"
    for i, issue in enumerate(drift_data['validation_drift']['violations'], 1):
        report += f"""#### Issue #{i}: {issue['issue']}

- **Endpoint:** `{issue['endpoint']}`
- **Severity:** {issue['severity']}
- **Tests Affected:** {issue['test_cases_affected']}
- **Confidence:** {issue['confidence']:.0%}

"""

    # Add root cause analysis
    report += "\n---\n\n## 🔍 Root Cause Analysis\n\n"

    for i, rc in enumerate(root_causes['root_causes'], 1):
        report += f"""### Root Cause #{i}: {rc['pattern'].replace('_', ' ').title()}

**Endpoint:** `{rc['endpoint']}`
**Confidence:** {rc['confidence'].upper()}

**Hypothesis:**
{rc['hypothesis']}

**Why This Happened:**
{rc['why']}

**Evidence:**
"""
        for evidence in rc['evidence']:
            report += f"- {evidence}\n"

        report += f"""
**Recommended Fix:**
{rc['remediation']['description']}

**Code Example:**
```python
{rc['remediation']['code_example']}
```

**Implementation Steps:**
"""
        if 'steps' in rc['remediation']:
            for step in rc['remediation']['steps']:
                report += f"{step}\n"

        report += f"""
**Estimated Effort:** {rc['remediation']['estimated_effort'].upper()}
**Priority:** {rc['remediation']['priority'].upper()}

---

"""

    # Add summary insights
    report += f"""## 💡 Key Insights

### Systemic Issues Detected

"""
    for issue in root_causes['summary']['systemic_issues']:
        report += f"- {issue}\n"

    report += f"""
### Quick Wins (High Impact, Low Effort)

"""
    for win in root_causes['summary']['quick_wins']:
        report += f"- ✅ {win}\n"

    report += """
---

## 📈 Next Steps

1. **Immediate:** Fix the 2 HIGH severity contract drift issues (estimated 15 minutes)
2. **Short-term:** Add input validation for POST endpoints (estimated 30 minutes)
3. **Medium-term:** Implement automated schema validation tests
4. **Long-term:** Set up continuous drift monitoring in CI/CD

---

## 📚 Additional Resources

- **JSON Report:** `drift_report.json` (machine-readable data)
- **Root Cause Analysis:** `root_cause_analysis.json` (detailed patterns)
- **Test Results:** `test_results/` directory
- **Progressive Drift History:** `progressive_drift/drift_history.jsonl`

---

**Framework:** API Behavioral Drift Detection v0.2.0
**Detection Methods:** Symbolic (Contract) + Rule-based (Validation) + ML (Behavioral)
**Confidence Scoring:** Pattern-based with evidence weighting
"""

    return report

def run_standalone_demo():
    """Run complete standalone demo."""
    print("=" * 80)
    print("API BEHAVIORAL DRIFT DETECTION - STANDALONE DEMO")
    print("=" * 80)
    print()

    # Setup
    demo_path = Path("demo/sample_demo")
    create_demo_directories(demo_path)

    # Create OpenAPI spec
    print("📝 Creating sample OpenAPI specification...")
    spec = create_sample_openapi_spec()
    spec_file = demo_path / "config" / "openapi_spec.json"
    with open(spec_file, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f"✅ Saved spec to: {spec_file}")

    # Generate drift detection results
    print("\n🔍 Simulating drift detection...")
    drift_data = generate_simulated_drift_issues()

    # Generate root cause analysis
    print("🧠 Running root cause analysis...")
    root_causes = generate_root_cause_analysis()

    # Save JSON reports
    print("\n💾 Saving results...")

    # Drift report JSON
    drift_json_file = demo_path / "results" / "drift_report.json"
    with open(drift_json_file, 'w') as f:
        json.dump(drift_data, f, indent=2)
    print(f"✅ Drift report (JSON): {drift_json_file}")

    # Root cause JSON
    rca_json_file = demo_path / "results" / "root_cause_analysis.json"
    with open(rca_json_file, 'w') as f:
        json.dump(root_causes, f, indent=2)
    print(f"✅ Root cause analysis (JSON): {rca_json_file}")

    # Markdown report
    markdown_report = create_markdown_report(drift_data, root_causes)
    md_file = demo_path / "results" / "drift_report.md"
    with open(md_file, 'w') as f:
        f.write(markdown_report)
    print(f"✅ Drift report (Markdown): {md_file}")

    # Save progressive drift snapshot
    drift_snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contract_drift_score": drift_data['contract_drift']['score'],
        "validation_drift_score": drift_data['validation_drift']['score'],
        "behavioral_drift_score": drift_data['behavioral_drift']['score'],
        "overall_drift_score": drift_data['overall_drift_score'],
        "tests_passed": drift_data['tests_passed'],
        "tests_failed": drift_data['tests_failed']
    }

    drift_history_file = demo_path / "results" / "progressive_drift" / "drift_history.jsonl"
    with open(drift_history_file, 'a') as f:
        f.write(json.dumps(drift_snapshot) + '\n')
    print(f"✅ Progressive drift snapshot: {drift_history_file}")

    # Create test results breakdown
    test_results = {
        "contract_drift_tests": {
            "total": 10,
            "passed": 3,
            "failed": 7,
            "failures": [v['issue'] for v in drift_data['contract_drift']['violations']]
        },
        "validation_drift_tests": {
            "total": 8,
            "passed": 5,
            "failed": 3,
            "failures": [v['issue'] for v in drift_data['validation_drift']['violations']]
        },
        "behavioral_drift_tests": {
            "total": 7,
            "passed": 7,
            "failed": 0,
            "anomalies": [a['issue'] for a in drift_data['behavioral_drift']['anomalies']]
        }
    }

    test_results_file = demo_path / "results" / "test_results" / "summary.json"
    with open(test_results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"✅ Test results summary: {test_results_file}")

    # Create README for results
    results_readme = f"""# Demo Results - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Files in This Directory

- **drift_report.md** - Human-readable drift analysis report
- **drift_report.json** - Machine-readable drift data
- **root_cause_analysis.json** - Pattern-based root cause analysis with code fixes
- **test_results/** - Detailed test execution results
- **progressive_drift/drift_history.jsonl** - Time-series drift data

## Quick View

```bash
# Read the main report
cat drift_report.md

# View JSON data
cat drift_report.json | python -m json.tool

# Check root causes
cat root_cause_analysis.json | python -m json.tool

# View drift trend
cat progressive_drift/drift_history.jsonl
```

## Key Findings

- Overall Drift Score: {drift_data['overall_drift_score']:.2f}
- Critical Issues: {len([v for v in drift_data['contract_drift']['violations'] if v['severity'] == 'HIGH'])}
- Tests Failed: {drift_data['tests_failed']}/{drift_data['total_tests_executed']}

## Next Steps

See drift_report.md for detailed recommendations and code examples.
"""

    readme_file = demo_path / "results" / "README.md"
    with open(readme_file, 'w') as f:
        f.write(results_readme)
    print(f"✅ Results README: {readme_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print()
    print(f"📁 Results saved to: {demo_path / 'results'}")
    print()
    print("📊 Summary:")
    print(f"  - Overall Drift Score: {drift_data['overall_drift_score']:.2f}")
    print(f"  - Contract Drift: {drift_data['contract_drift']['score']:.2f} ({len(drift_data['contract_drift']['violations'])} issues)")
    print(f"  - Validation Drift: {drift_data['validation_drift']['score']:.2f} ({len(drift_data['validation_drift']['violations'])} issues)")
    print(f"  - Behavioral Drift: {drift_data['behavioral_drift']['score']:.2f} ({len(drift_data['behavioral_drift']['anomalies'])} anomalies)")
    print(f"  - Root Causes Found: {len(root_causes['root_causes'])}")
    print(f"  - Tests: {drift_data['tests_passed']}/{drift_data['total_tests_executed']} passed")
    print()
    print("📖 View Results:")
    print(f"  - Report: cat {md_file}")
    print(f"  - JSON: cat {drift_json_file} | python -m json.tool")
    print(f"  - Root Causes: cat {rca_json_file} | python -m json.tool")
    print()
    print("🎉 Demo completed successfully!")
    print()

if __name__ == "__main__":
    try:
        run_standalone_demo()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
