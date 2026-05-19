# Demo Results - 2026-05-09 01:18:10 UTC

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

- Overall Drift Score: 0.42
- Critical Issues: 2
- Tests Failed: 10/25

## Next Steps

See drift_report.md for detailed recommendations and code examples.
