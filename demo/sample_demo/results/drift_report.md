# API Behavioral Drift Detection Report

**Generated:** 2026-05-09 01:18:10 UTC
**API:** Demo User API v1.0.0
**Base URL:** http://localhost:8000

---

## 📊 Executive Summary

- **Overall Drift Score:** 0.42 (MODERATE)
- **Total Issues Found:** 8
- **Tests Executed:** 25
- **Tests Passed:** 15 (60.0%)
- **Tests Failed:** 10 (40.0%)

### Drift Breakdown

| Type | Score | Issues | Severity |
|------|-------|--------|----------|
| Contract Drift | 0.35 | 3 | 🔴 HIGH |
| Validation Drift | 0.28 | 3 | 🟡 MEDIUM |
| Behavioral Drift | 0.15 | 2 | 🟢 LOW |

---

## 🔥 Critical Issues

### Contract Drift Issues

#### Issue #1: Missing required field 'email' in response

- **Endpoint:** `POST /users`
- **Severity:** HIGH
- **Tests Affected:** 5
- **Confidence:** 95%

#### Issue #2: Unexpected field 'internal_id' found in response

- **Endpoint:** `GET /users/{userId}`
- **Severity:** MEDIUM
- **Tests Affected:** 3
- **Confidence:** 88%

#### Issue #3: Type mismatch: field 'age' expected integer, got string

- **Endpoint:** `POST /users`
- **Severity:** HIGH
- **Tests Affected:** 4
- **Confidence:** 92%


### Validation Drift Issues

#### Issue #1: Accepts invalid email format 'not-an-email'

- **Endpoint:** `POST /users`
- **Severity:** MEDIUM
- **Tests Affected:** 3
- **Confidence:** 90%

#### Issue #2: Accepts negative age value (-5)

- **Endpoint:** `POST /users`
- **Severity:** MEDIUM
- **Tests Affected:** 2
- **Confidence:** 85%

#### Issue #3: Accepts name exceeding max length (150 chars when max is 100)

- **Endpoint:** `POST /users`
- **Severity:** LOW
- **Tests Affected:** 2
- **Confidence:** 80%


---

## 🔍 Root Cause Analysis

### Root Cause #1: Missing Required Field

**Endpoint:** `POST /users`
**Confidence:** HIGH

**Hypothesis:**
Required field 'email' is missing from API response. The field is defined in the specification but never returned by the implementation.

**Why This Happened:**
The API implementation likely forgot to include the field in the response serializer or database query projection.

**Evidence:**
- Test case test_001: email field absent
- Test case test_003: email field absent
- Test case test_007: email field absent

**Recommended Fix:**
Include the email field in the UserResponse serializer

**Code Example:**
```python
# Fix for missing email field

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
    )
```

**Implementation Steps:**
1. Open the user serializer/response model file
2. Add 'email: str' field to the response schema
3. Update the endpoint handler to include email in the response
4. Run tests to verify the fix
5. Update OpenAPI spec if needed

**Estimated Effort:** LOW
**Priority:** HIGH

---

### Root Cause #2: Type Mismatch

**Endpoint:** `POST /users`
**Confidence:** HIGH

**Hypothesis:**
Field 'age' has type mismatch. Expected integer but got string.

**Why This Happened:**
Type coercion issue in serializer, database schema returns string, or incorrect type casting in business logic.

**Evidence:**
- Test case test_004: age='25' (string) instead of 25 (int)
- Test case test_005: age='30' (string) instead of 30 (int)

**Recommended Fix:**
Ensure age field is properly typed as integer in serializer

**Code Example:**
```python
# Fix for type mismatch

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
    )
```

**Implementation Steps:**

**Estimated Effort:** LOW
**Priority:** HIGH

---

### Root Cause #3: Missing Input Validation

**Endpoint:** `POST /users`
**Confidence:** MEDIUM

**Hypothesis:**
Endpoint accepts invalid input that should be rejected. Missing validation for email format and age constraints.

**Why This Happened:**
Validation middleware not applied, or validator configuration incomplete.

**Evidence:**
- Test case test_invalid_001: Accepted invalid email 'not-an-email'
- Test case test_invalid_002: Accepted negative age -5

**Recommended Fix:**
Add Pydantic validators for email and age fields

**Code Example:**
```python
# Add validation

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
        return v
```

**Implementation Steps:**

**Estimated Effort:** MEDIUM
**Priority:** MEDIUM

---

## 💡 Key Insights

### Systemic Issues Detected

- Multiple serializers missing required fields - consider implementing automated schema validation tests
- Input validation gaps across POST endpoints - recommend adding a validation middleware layer

### Quick Wins (High Impact, Low Effort)

- ✅ Add email field to UserResponse (5 minutes, fixes 3 test failures)
- ✅ Fix age type conversion (10 minutes, fixes 2 test failures)

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
