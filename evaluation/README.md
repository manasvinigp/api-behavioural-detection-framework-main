# Evaluation Framework

This directory contains the evaluation framework for benchmarking the API Behavioral Drift Detection system.

## Structure

```
evaluation/
├── datasets/           # Benchmark datasets
│   ├── synthetic/     # Synthetic APIs with injected drift
│   ├── real_world/    # Real API snapshots
│   └── timeseries/    # Time-series API evolution data
├── baselines/         # Baseline tool comparisons
│   ├── dredd/         # Dredd OpenAPI validator
│   ├── schemathesis/  # Property-based testing
│   └── postman/       # Postman contract testing
├── metrics/           # Evaluation metrics
│   ├── precision_recall.py
│   ├── false_positive_rate.py
│   └── coverage_analysis.py
└── scripts/           # Evaluation scripts
    ├── run_evaluation.py
    ├── compare_baselines.py
    └── generate_report.py
```

## Usage

### Run Full Evaluation

```bash
python evaluation/scripts/run_evaluation.py --dataset all
```

### Compare with Baselines

```bash
python evaluation/scripts/compare_baselines.py --methods dredd,schemathesis,ours
```

### Generate LaTeX Tables

```bash
python evaluation/scripts/generate_report.py --format latex --output results/
```

## Datasets

### Synthetic Dataset

Controlled experiments with injected drift:
- Contract drift: Remove fields, change types
- Validation drift: Remove validation logic
- Behavioral drift: Add latency, randomize responses

### Real-World Dataset

Snapshots of production APIs:
- GitHub API v3
- Stripe API
- Twilio API
- OpenWeatherMap API

### Time-Series Dataset

Historical API responses over time:
- Daily snapshots for 90 days
- Track progressive drift
- Detect change points

## Metrics

### Per-Drift-Type Metrics

For each drift type (contract, validation, behavioral, progressive):

- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1 Score**: 2 * (Precision * Recall) / (Precision + Recall)

### Overall Metrics

- **False Positive Rate**: FP / (FP + TN)
- **Detection Latency**: Time from drift injection to detection
- **Edge Case Coverage**: % of edge cases detected

## Baseline Comparisons

| Tool | Approach | Contract Drift | Validation Drift | Behavioral Drift |
|------|----------|----------------|------------------|------------------|
| Dredd | Schema validation | ✅ High | ❌ None | ❌ None |
| Schemathesis | Property-based | ✅ High | ✅ Medium | ❌ None |
| Postman | Manual tests | ✅ Medium | ✅ Medium | ❌ None |
| **Ours (Hybrid)** | Symbolic + ML | ✅ High | ✅ High | ✅ High |

## Reproducibility

All experiments are fully reproducible:

1. **Fixed random seeds**: Set in config
2. **Version pinning**: requirements-eval.txt
3. **Docker containers**: Dockerfile.eval
4. **Detailed logs**: All hyperparameters logged

## Expected Results

### Target Metrics (for publication)

- **Contract Drift F1**: > 0.90
- **Validation Drift F1**: > 0.85
- **Behavioral Drift F1**: > 0.80
- **False Positive Rate**: < 5%
- **Detection Latency**: < 1 minute

### Ablation Studies

Test each component independently:

1. **Symbolic only**: Contract + Validation drift
2. **Statistical only**: Behavioral drift (divergence)
3. **ML only**: Behavioral drift (embeddings)
4. **Hybrid (all)**: Best overall performance

## Research Questions

1. Does multi-fidelity input (OpenAPI + PRD) improve accuracy?
2. What is the optimal weight distribution for unified drift score?
3. How does confidence scoring affect precision/recall tradeoff?
4. Can we detect drift before it impacts users?

## Citation

If you use this evaluation framework, please cite:

```bibtex
@inproceedings{api-behavioral-drift-2026,
  title={Multi-Dimensional API Behavioral Drift Detection: A Hybrid Approach},
  author={[Your Name]},
  booktitle={Proceedings of [Conference]},
  year={2026}
}
```
