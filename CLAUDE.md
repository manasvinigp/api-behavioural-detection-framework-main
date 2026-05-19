# API Behavioral Drift Detection Framework - Claude Assistant Guide

## Project Overview

This is a **research-grade system** for detecting **multi-dimensional API drift** using hybrid approaches that go beyond traditional schema validation. The goal is to model and monitor **API behavior**, not just static contracts.

**Core Purpose:** Detect behavioral inconsistencies, logical violations, and progressive degradation that traditional OpenAPI validators miss.

---

## 🎯 Research Objectives

This framework aims to produce a **Q1-level academic publication** with these novel contributions:

1. **Multi-fidelity contract fusion** - Combine OpenAPI specs with PRD natural language
2. **Hybrid drift detection** - Symbolic + Statistical + ML methods
3. **Behavioral modeling** - Learn expected API behavior from incomplete specs
4. **Progressive drift tracking** - Time-series anomaly detection for APIs
5. **Explainable drift analysis** - Root cause identification with confidence scores

---

## 🧩 Key Concepts

### 1. Multi-Dimensional Drift Types

#### Contract Drift (Symbolic)
- **Definition**: API responses deviate from schema specification
- **Detection**: Rule-based schema validation
- **Examples**: Missing required fields, type mismatches, unexpected fields

#### Validation Drift (Rule-based)
- **Definition**: API accepts invalid inputs it should reject
- **Detection**: Test with constraint-violating inputs, expect 4xx
- **Examples**: Missing email validation, accepting negative ages, no length checks

#### Behavioral Drift (ML + Statistical)
- **Definition**: Inconsistent API behavior for same/similar inputs
- **Detection**: Embedding similarity, statistical divergence
- **Examples**: Same input → different outputs, response time degradation

#### Progressive Drift (Time-series)
- **Definition**: Gradual API degradation over time
- **Detection**: Change point detection, trend analysis
- **Examples**: Increasing latency, rising error rates, schema evolution

---

### 2. Multi-Fidelity Input Processing

#### High-Fidelity Input: OpenAPI Specification
- Structured, machine-readable
- Explicit constraints (types, enums, ranges)
- **Confidence: 1.0** (fully trusted)

#### Low-Fidelity Input: Product Requirements Documents (PRDs)
- Unstructured natural language
- Implicit constraints extracted via NLP
- **Confidence: 0.6-0.9** (inferred, needs scoring)

#### Unified Contract Representation (ICR)
Merge both inputs into a single graph-based model:
```python
Contract = {
    "endpoints": {
        "POST:/users": {
            "fields": {
                "email": {
                    "type": "string",
                    "pattern": "email",
                    "required": True,
                    "source": "openapi",
                    "confidence": 1.0
                },
                "age": {
                    "type": "integer",
                    "min": 18,
                    "max": 120,
                    "source": "prd",  # Extracted from text
                    "confidence": 0.85
                }
            }
        }
    }
}
```

---

### 3. Intelligent Test Generation

#### Generation Methods

**Rule-Based (Baseline)**
- Direct constraint extraction
- Deterministic test creation
- Fast, no external dependencies

**Constraint Solving (SMT-style)**
- Generate inputs satisfying complex constraints
- Handle cross-field dependencies
- Example: Z3 solver for constraint satisfaction

**LLM-Assisted (Semantic)**
- Understand business logic from PRDs
- Generate adversarial test cases
- Example: "User under 18 should not be able to purchase alcohol"

#### Test Categories

1. **Valid Cases**: Expected inputs that should return 2xx
2. **Invalid Cases**: Constraint violations that should return 4xx
3. **Boundary Cases**: Min/max values, edge conditions
4. **Cross-field Dependencies**: Complex constraint interactions
5. **Semantic Adversarial**: Business-logic violations

---

### 4. Hybrid Detection Architecture

```
Symbolic Layer (Deterministic)
├── Schema validation
├── Type checking
└── Constraint verification
    ↓
Statistical Layer
├── Distribution divergence (KL, JS)
├── Anomaly detection (Isolation Forest)
└── Change point detection
    ↓
Machine Learning Layer
├── Response embeddings
├── Behavioral clustering
└── Progressive drift prediction
```

**Why Hybrid?**
- **Symbolic**: High precision, explainable, no training data needed
- **Statistical**: Detects gradual changes, no assumptions about distribution
- **ML**: Learns complex patterns, generalizes across APIs

---

## 🏗️ Architecture Quick Reference

```
input/                  → Parse OpenAPI & PRD, build unified contract
  ├── openapi/         → YAML/JSON parser
  └── prd/             → NLP extraction (spaCy/Transformers)

schema/                → Contract modeling & graph representation
  ├── contract/        → ICR builder
  └── graph/           → Dependency graphs (NetworkX)

generation/            → Intelligent test generation
  ├── valid/           → Happy-path cases
  ├── invalid/         → Constraint violations
  ├── boundary/        → Edge cases
  ├── semantic/        → LLM-assisted generation
  └── prioritizer/     → Risk-based ordering

execution/             → Parallel test execution
  └── runner/          → HTTP executor with retry logic

analysis/              → Multi-dimensional drift detection
  ├── drift/           → 4 drift detectors
  │   ├── contract.py      (Symbolic)
  │   ├── validation.py    (Rule-based)
  │   ├── behavioral.py    (ML + Statistical)
  │   └── progressive.py   (Time-series)
  └── reasoning/       → Root cause analysis (LLM-assisted)

ml/                    → Machine learning components
  ├── embedding/       → Response embeddings
  ├── clustering/      → Behavioral clustering
  └── anomaly/         → Outlier detection

reporting/             → Output generation
  ├── markdown/        → Human-readable reports
  ├── json/            → Machine-readable data
  └── visualization/   → Drift plots and charts
```

---

## 💡 Development Guidelines

### When Adding New Features

1. **Maintain modularity** - Each component should work independently
2. **Support reproducibility** - All experiments must be repeatable
3. **Add evaluation metrics** - How do you measure success?
4. **Document research rationale** - Why this approach vs alternatives?
5. **Provide baselines** - Compare against existing methods

### Code Style

- **Clear separation**: Symbolic vs Statistical vs ML
- **Confidence scoring**: All inferred constraints need confidence values
- **Explainability**: Every drift detection must explain WHY
- **Type hints**: Use Python type annotations everywhere
- **Docstrings**: Document all public APIs

### Testing Requirements

```bash
# Unit tests for each module
pytest tests/unit/

# Integration tests for pipelines
pytest tests/integration/

# Evaluation on benchmark datasets
pytest tests/evaluation/

# All tests must pass before commit
pytest --cov=api_contract_validator --cov-report=html
```

---

## 🧪 Research Components

### 1. PRD → Contract Extraction (NLP)

**Goal**: Extract API contracts from natural language requirements

**Approach**:
- Named Entity Recognition (NER) for field names
- Relation Extraction for constraints
- Pattern matching for validation rules
- Confidence scoring based on linguistic certainty

**Example**:
```
Input (PRD text):
"The email field must be a valid email address and is required."

Output (Contract):
{
    "email": {
        "type": "string",
        "pattern": "^[^@]+@[^@]+\\.[^@]+$",
        "required": true,
        "confidence": 0.92,
        "source": "prd"
    }
}
```

**Libraries**: spaCy, HuggingFace Transformers, regex

---

### 2. Behavioral Modeling (ML)

**Goal**: Learn `P(output | input)` from historical API responses

**Approach**:
- Embed requests and responses using sentence transformers
- Cluster similar behaviors
- Detect anomalies (responses far from cluster centroids)

**Example**:
```python
from api_contract_validator.ml.behavioral import BehaviorModel

model = BehaviorModel(embedding_model="all-MiniLM-L6-v2")
model.train(historical_api_responses)

# Predict expected response
expected_embedding = model.predict(request_input)
actual_embedding = model.embed(actual_response)

# Compute drift
drift_score = 1 - cosine_similarity(expected_embedding, actual_embedding)
```

**Libraries**: sentence-transformers, scikit-learn, PyTorch

---

### 3. Statistical Drift Detection

**Goal**: Detect distribution changes in API responses

**Methods**:
- **KL Divergence**: Measure distribution shift
- **Jensen-Shannon Divergence**: Symmetric version of KL
- **Kolmogorov-Smirnov Test**: Non-parametric distribution comparison
- **Isolation Forest**: Anomaly detection for outlier responses

**Example**:
```python
from api_contract_validator.analysis.drift.behavioral import StatisticalDriftDetector

detector = StatisticalDriftDetector()
baseline_responses = load_baseline()
current_responses = api.call_multiple(test_cases)

drift_score = detector.compute_js_divergence(baseline_responses, current_responses)
# drift_score > 0.1 indicates significant drift
```

**Libraries**: scipy.stats, scikit-learn

---

### 4. Progressive Drift Tracking (Time-Series)

**Goal**: Detect gradual API degradation over time

**Approach**:
- Store API response metrics in time-series database
- Apply change point detection algorithms
- Predict future drift using LSTM/Prophet

**Example**:
```python
from api_contract_validator.analysis.drift.progressive import ProgressiveDriftTracker

tracker = ProgressiveDriftTracker(window_size=100)

for result in continuous_validation_stream:
    tracker.record(result.response_time, result.error_rate, result.timestamp)
    
    if tracker.detect_change_point():
        alert(f"Response time increased by {tracker.change_magnitude}%")
```

**Libraries**: ruptures (change point detection), Prophet, LSTM (PyTorch)

---

## 📊 Drift Scoring System

### Unified Drift Score

```python
DriftScore = w1 * contract_drift + w2 * validation_drift + w3 * behavioral_drift + w4 * progressive_drift
```

**Default weights** (configurable):
- `w1 = 0.3` (contract)
- `w2 = 0.4` (validation - highest priority)
- `w3 = 0.2` (behavioral)
- `w4 = 0.1` (progressive)

### Per-Dimension Scoring

#### Contract Drift Score
```python
contract_drift_score = violations / total_fields
# violations: missing fields, type mismatches, extra fields
```

#### Validation Drift Score
```python
validation_drift_score = invalid_accepted / total_invalid_tests
# invalid_accepted: 2xx responses to intentionally invalid inputs
```

#### Behavioral Drift Score
```python
behavioral_drift_score = 1 - avg(cosine_similarity(expected, actual))
# Using embedding-based similarity
```

#### Progressive Drift Score
```python
progressive_drift_score = statistical_divergence(current_window, baseline_window)
# Using JS divergence on time-series data
```

---

## 🎯 Root Cause Analysis

### Explainability Requirements

Every drift detection must provide:

1. **What drifted**: Specific field, endpoint, behavior
2. **Why it drifted**: Hypothesis + evidence
3. **Confidence**: How certain are we? (0-1 score)
4. **Remediation**: Suggested fix with code example

### Analysis Framework

```python
class DriftExplanation:
    what: str           # "Field 'email' missing in response"
    why: str            # "API forgot to include field in serializer"
    confidence: float   # 0.85
    evidence: List[str] # ["8/10 test cases missing email", "Other fields present"]
    remediation: str    # "Add email to UserSerializer output"
    code_example: str   # Python code snippet
```

### Root Cause Templates

Use pattern matching + LLM analysis:

**Pattern 1: Missing Required Field**
```
Hypothesis: API implementation missing field serialization
Evidence: Field defined in spec, always absent in responses
Confidence: HIGH (0.9)
Fix: Add field to response serializer
```

**Pattern 2: Validation Drift**
```
Hypothesis: Missing input validation middleware
Evidence: All POST endpoints accept invalid inputs
Confidence: MEDIUM (0.7)
Fix: Add Pydantic validation models
```

**Pattern 3: Behavioral Drift**
```
Hypothesis: Database query performance degradation
Evidence: Response time increased 40% over 7 days
Confidence: MEDIUM (0.6)
Fix: Add database index, analyze query plan
```

---

## 🔬 Evaluation Framework

### Datasets

1. **Synthetic APIs** - Controlled drift injection
2. **Real-world snapshots** - GitHub API, Stripe API, etc.
3. **Time-series data** - Historical API responses

### Baseline Comparisons

Compare against:
- **Dredd**: OpenAPI validation tool
- **Schemathesis**: Property-based testing
- **Postman**: Contract testing
- **Our framework**: Multi-dimensional drift detection

### Metrics

#### Per-Drift-Type Metrics
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = 2 * (Precision * Recall) / (Precision + Recall)

#### Overall Metrics
- False positive rate
- Detection latency
- Edge case coverage

### Running Evaluation

```bash
# Full evaluation pipeline
python evaluation/run_evaluation.py --dataset all

# Compare with baselines
python evaluation/compare_baselines.py --methods dredd,schemathesis,ours

# Generate LaTeX tables for paper
python evaluation/generate_latex_tables.py
```

---

## 🚀 Quick Command Reference

### Development Commands

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=api_contract_validator --cov-report=html

# Type checking
mypy src/

# Code formatting
black src/ tests/

# Linting
ruff check src/ tests/
```

### Validation Commands

```bash
# Basic validation
acv validate --spec api/openapi.yaml --url http://localhost:8000

# Multi-fidelity validation (OpenAPI + PRD)
acv validate --spec api/openapi.yaml --prd requirements/api.md --url http://localhost:8000

# Track progressive drift
acv validate --spec api/openapi.yaml --url http://localhost:8000 --track-drift

# Compare against baseline
acv validate --spec api/openapi.yaml --url http://localhost:8000 --baseline reports/baseline.json
```

### Evaluation Commands

```bash
# Run evaluation
python evaluation/run_evaluation.py --dataset synthetic

# Generate report
python evaluation/generate_report.py --output results/

# Visualize drift
python evaluation/visualize_drift.py --input results/drift_data.json
```

---

## 🎓 Research Best Practices

### 1. Separate Concerns

- **Symbolic methods** → `analysis/drift/contract.py`, `analysis/drift/validation.py`
- **Statistical methods** → `analysis/drift/behavioral.py` (divergence, anomaly)
- **ML methods** → `ml/` (embedding, clustering, prediction)

### 2. Confidence Scoring

All non-deterministic components must output confidence:

```python
class DriftResult:
    is_drift: bool
    confidence: float  # 0.0 - 1.0
    method: str        # "symbolic" | "statistical" | "ml"
```

### 3. Ablation Studies

Evaluate each component independently:

```python
# Test contract drift detector alone
results_contract_only = evaluate(contract_detector, dataset)

# Test validation drift detector alone
results_validation_only = evaluate(validation_detector, dataset)

# Test combined system
results_combined = evaluate(full_system, dataset)
```

### 4. Reproducibility

All experiments must be reproducible:

- **Fixed random seeds** for ML components
- **Version pinning** in requirements.txt
- **Docker containers** for evaluation environment
- **Detailed logging** of all hyperparameters

---

## 📚 Further Reading

### Academic Context

This framework builds on:

1. **Contract Testing**: Design by Contract (Meyer, 1992)
2. **Property-Based Testing**: QuickCheck (Claessen & Hughes, 2000)
3. **Metamorphic Testing**: Chen et al. (1998)
4. **API Evolution**: Dig & Johnson (2006)
5. **Behavioral Drift**: Concept drift in ML (Widmer & Kubat, 1996)

### Related Work

- **Dredd**: HTTP API validation
- **Schemathesis**: Property-based API testing
- **Pact**: Consumer-driven contract testing
- **Spring Cloud Contract**: JVM contract testing

### Novel Contributions (This Work)

1. **Multi-fidelity fusion** of OpenAPI + PRD
2. **Hybrid detection** (symbolic + statistical + ML)
3. **Behavioral modeling** from incomplete specs
4. **Progressive drift** tracking with time-series analysis
5. **Explainable drift** with confidence-scored root causes

---

## 🤝 Collaboration Guidelines

### For Researchers

- Propose new drift detection methods in `analysis/drift/`
- Add evaluation datasets in `evaluation/datasets/`
- Contribute baseline comparisons
- Document novel algorithms in comments + docstrings

### For Engineers

- Improve performance (parallel execution, caching)
- Add support for new input formats (GraphQL, gRPC)
- Enhance reporting (interactive dashboards)
- CI/CD integrations

### For ML Practitioners

- Experiment with different embedding models
- Try new anomaly detection algorithms
- Improve behavioral clustering
- Add transfer learning across APIs

---

## 📊 Success Criteria

This project is successful if:

1. ✅ **Detects drift missed by baselines** (Dredd, Schemathesis)
2. ✅ **F1 score > 0.85** on synthetic evaluation dataset
3. ✅ **Low false positive rate** (<5%) on real-world APIs
4. ✅ **Explainable outputs** with confidence scores
5. ✅ **Reproducible evaluation** with published datasets
6. ✅ **Accepted to Q1 conference/journal** (ICSE, FSE, ASE, TSE, TOSEM)

---

## 🔮 Future Directions

### Planned Enhancements (v0.3+)

1. **Causal Inference** for root cause analysis
2. **Reinforcement Learning** for test prioritization
3. **Transfer Learning** across similar APIs
4. **API Embedding Space** for cross-API analysis
5. **Active Learning** to request human labels for uncertain cases

### Research Questions

- How to quantify "behavioral equivalence" of API changes?
- Can we predict API drift before it happens?
- What is the optimal weight distribution for unified drift score?
- How to handle APIs with non-deterministic behavior?

---

**This is a research project. Prioritize scientific rigor over rapid feature development.**

*Last Updated: 2026-04-29*
