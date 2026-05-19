# Research Methodology

## Problem Statement

Traditional API validation tools only detect **schema-level drift** (missing fields, type mismatches) but miss:

1. **Validation Drift**: API accepts invalid inputs it should reject
2. **Behavioral Drift**: Inconsistent API behavior for same/similar inputs
3. **Progressive Drift**: Gradual API degradation over time

**Research Question**: Can a hybrid approach (symbolic + statistical + ML) detect multi-dimensional API drift more effectively than existing tools?

---

## Novel Contributions

### 1. Multi-Fidelity Contract Fusion

**Problem**: APIs often have incomplete specifications. OpenAPI specs are structured but may be outdated, while PRDs contain unstructured requirements.

**Solution**: Merge both inputs into a Unified Contract Representation (ICR) with confidence scoring.

**Approach**:
- Parse OpenAPI → high-confidence constraints (1.0)
- Extract from PRD using NLP → medium-confidence constraints (0.6-0.9)
- Merge with conflict resolution (higher confidence wins)

**Evaluation**: Compare drift detection accuracy with vs without PRD fusion.

---

### 2. Hybrid Drift Detection Architecture

**Problem**: Symbolic methods have high precision but low recall (miss subtle drift). ML methods have high recall but low precision (false positives).

**Solution**: Three-layer hybrid architecture:

#### Layer 1: Symbolic Detection (High Precision)
- Contract drift: Schema validation
- Validation drift: Constraint checking
- **Confidence**: 1.0 (deterministic)

#### Layer 2: Statistical Detection (Balanced)
- Behavioral drift: KL/JS divergence
- Anomaly detection: Isolation Forest
- **Confidence**: 0.7-0.9 (p-value based)

#### Layer 3: ML Detection (High Recall)
- Behavioral drift: Embedding similarity
- Progressive drift: LSTM prediction
- **Confidence**: 0.5-0.8 (model uncertainty)

**Evaluation**: Ablation study to measure contribution of each layer.

---

### 3. Behavioral Modeling from Incomplete Specs

**Problem**: When specs are incomplete, how do we know what "correct" behavior looks like?

**Solution**: Learn expected behavior from historical API responses.

**Approach**:
1. Embed responses using sentence transformers
2. Cluster similar behaviors
3. Detect anomalies (responses far from clusters)

**Evaluation**: Compare against ground truth on synthetic dataset.

---

### 4. Progressive Drift Tracking

**Problem**: APIs drift gradually, making single-snapshot detection insufficient.

**Solution**: Time-series analysis with change point detection.

**Approach**:
1. Store response metrics (latency, error rate, schema) over time
2. Apply PELT (Pruned Exact Linear Time) change point detection
3. Predict future drift using Prophet/LSTM

**Evaluation**: Inject gradual drift in synthetic API, measure detection latency.

---

### 5. Explainable Drift Analysis

**Problem**: Detecting drift is not enough—developers need actionable insights.

**Solution**: Root cause analysis with confidence-scored explanations.

**Approach**:
1. Pattern matching for common drift types
2. LLM-assisted causal inference
3. Remediation suggestions with code examples

**Evaluation**: Human study—do developers find explanations actionable?

---

## Experimental Design

### Datasets

#### 1. Synthetic Dataset (Controlled)
- **Purpose**: Ablation studies, precision/recall measurement
- **Size**: 100 synthetic APIs
- **Drift Injection**:
  - Contract drift: Remove fields (10%), change types (10%)
  - Validation drift: Remove constraints (20%)
  - Behavioral drift: Add latency (15%), randomize responses (10%)
- **Ground Truth**: Known drift injections

#### 2. Real-World Dataset (Naturalistic)
- **Purpose**: Generalization, false positive rate
- **APIs**: GitHub, Stripe, Twilio, OpenWeatherMap
- **Collection**: Monthly snapshots over 1 year
- **Labeling**: Manual review by 3 engineers

#### 3. Time-Series Dataset (Progressive)
- **Purpose**: Change point detection, detection latency
- **Collection**: Daily snapshots for 90 days
- **Drift**: Gradual degradation (latency, error rate)

---

### Baseline Comparisons

| Tool | Approach | Strengths | Limitations |
|------|----------|-----------|-------------|
| **Dredd** | Schema validation | Fast, deterministic | Only contract drift |
| **Schemathesis** | Property-based testing | Good coverage | No behavioral drift |
| **Postman** | Manual contract tests | User-defined | Manual, no ML |
| **Ours** | Hybrid (symbolic + ML) | Multi-dimensional | Requires training data |

---

### Evaluation Metrics

#### Per-Drift-Type Metrics

For each drift type D ∈ {contract, validation, behavioral, progressive}:

- **Precision**: P(D) = TP / (TP + FP)
- **Recall**: R(D) = TP / (TP + FN)
- **F1 Score**: F1(D) = 2 * P(D) * R(D) / (P(D) + R(D))

#### Overall Metrics

- **False Positive Rate**: FPR = FP / (FP + TN)
- **Detection Latency**: Time from drift injection to detection
- **Edge Case Coverage**: % of injected edge cases detected

#### Unified Drift Score

DriftScore = w1·F1(contract) + w2·F1(validation) + w3·F1(behavioral) + w4·F1(progressive)

**Hypothesis**: Optimal weights are w2 > w1 > w3 > w4 (validation drift most critical)

---

### Ablation Studies

Test each component independently:

1. **Symbolic only**: Contract + Validation drift detection
2. **Statistical only**: Behavioral drift (divergence methods)
3. **ML only**: Behavioral drift (embeddings)
4. **Hybrid (all)**: Full system

**Hypothesis**: Hybrid > ML > Statistical > Symbolic (for overall F1)

---

### Research Questions

#### RQ1: Does multi-fidelity input improve accuracy?

**Hypothesis**: F1(OpenAPI + PRD) > F1(OpenAPI only)

**Experiment**:
- Run evaluation with OpenAPI only
- Run evaluation with OpenAPI + PRD
- Compare F1 scores

**Expected Result**: +5-10% F1 improvement

---

#### RQ2: What is the optimal weight distribution?

**Hypothesis**: w2 (validation) should be highest

**Experiment**:
- Grid search over weight combinations
- Measure F1 on validation set
- Identify optimal weights

**Expected Result**: w2 ≈ 0.4, w1 ≈ 0.3, w3 ≈ 0.2, w4 ≈ 0.1

---

#### RQ3: How does confidence scoring affect precision/recall?

**Hypothesis**: Higher confidence threshold → higher precision, lower recall

**Experiment**:
- Vary confidence threshold from 0.5 to 1.0
- Plot precision-recall curve

**Expected Result**: Precision increases monotonically with threshold

---

#### RQ4: Can we detect drift before user impact?

**Hypothesis**: Yes, with time-series analysis

**Experiment**:
- Inject gradual drift in synthetic API
- Measure time from injection to detection
- Compare against user-reported issues (simulated)

**Expected Result**: Detection 1-7 days before user impact

---

## Threats to Validity

### Internal Validity

1. **Synthetic drift may not reflect real drift**: Mitigate by using real-world dataset
2. **Manual labeling may have errors**: Mitigate with 3-engineer consensus
3. **Hyperparameter tuning may overfit**: Mitigate with separate train/val/test split

### External Validity

1. **Limited to REST APIs**: Mitigate by discussing generalization to GraphQL/gRPC
2. **Limited to specific domains**: Test on diverse APIs (payments, social, weather)
3. **Requires historical data**: Discuss cold-start scenarios

### Construct Validity

1. **F1 may not capture all quality aspects**: Also measure detection latency, actionability
2. **Confidence scores may be miscalibrated**: Calibrate using Platt scaling

---

## Reproducibility Checklist

- ✅ Code publicly available on GitHub
- ✅ All dependencies pinned in requirements.txt
- ✅ Random seeds fixed in code
- ✅ Datasets included or downloadable
- ✅ Evaluation scripts provided
- ✅ Docker container for exact environment
- ✅ Detailed hyperparameters logged
- ✅ Raw results committed to repo

---

## Expected Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Implementation | 8 weeks | Core system + ML components |
| Evaluation | 4 weeks | Run all experiments, collect data |
| Analysis | 2 weeks | Statistical tests, plots |
| Writing | 6 weeks | Paper draft + revisions |
| **Total** | **20 weeks** | **Q1 conference submission** |

---

## Target Venues

### Tier 1 (Q1)

- **ICSE**: International Conference on Software Engineering
- **FSE**: Foundations of Software Engineering
- **ASE**: Automated Software Engineering
- **TSE**: IEEE Transactions on Software Engineering (journal)
- **TOSEM**: ACM Transactions on Software Engineering and Methodology (journal)

### Tier 2 (Q2)

- **ICSME**: International Conference on Software Maintenance and Evolution
- **MSR**: Mining Software Repositories
- **ISSTA**: International Symposium on Software Testing and Analysis

---

## Success Criteria

This research is successful if:

1. ✅ **F1 > 0.85** on all drift types (synthetic dataset)
2. ✅ **FPR < 5%** on real-world dataset
3. ✅ **Outperforms all baselines** by ≥10% F1
4. ✅ **Detects drift 1-7 days early** (progressive drift)
5. ✅ **Accepted to Q1 venue**

---

*Last Updated: 2026-04-30*
