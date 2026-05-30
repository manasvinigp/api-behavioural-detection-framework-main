"""Run PRD-driven validation for the demo shoppingassistant service.

This script merges the OpenAPI spec and a PRD document, generates tests,
executes them against the running demo service, and prints a short summary.

Run with the repo virtualenv Python:
.\.venv\Scripts\python.exe demo/test_demo/run_prd_validation.py
"""

from pathlib import Path
from api_contract_validator.input.factory import parse_with_type_hint
from api_contract_validator.input.openapi.parser import OpenAPIParser
from api_contract_validator.input.normalizer.models import UnifiedAPISpec, SourceType
from api_contract_validator.config.models import TestGenerationConfig, ExecutionConfig, Config
from api_contract_validator.generation.test_generator import MasterTestGenerator
from api_contract_validator.execution.runner.executor import TestExecutor
from api_contract_validator.execution.collector.result_collector import ResultCollector
from api_contract_validator.schema.contract.constraint_extractor import ConstraintExtractor
from api_contract_validator.analysis.drift.detector import DriftDetector
from api_contract_validator.analysis.reasoning.analyzer import AIAnalyzer
from api_contract_validator.reporting.generator import ReportGenerator


def main():
    openapi_path = Path("demo/test_demo/openapi/shoppingassistant.yaml")
    # Use the advanced PRD that intentionally diverges to trigger drift detection
    prd_path_hint = "prd:demo/test_demo/prd/shoppingassistant_prd_advanced.md"
    api_url = "http://127.0.0.1:8080"

    print("Parsing OpenAPI spec:", openapi_path)
    openapi_parser = OpenAPIParser()
    openapi_spec = openapi_parser.parse_file(openapi_path)
    print(f"  ✓ Parsed {len(openapi_spec.endpoints)} OpenAPI endpoints")

    print("Parsing PRD:", prd_path_hint)
    # Ensure PRD parser is registered (module import registers the adapter)
    try:
        import api_contract_validator.input.prd  # noqa: F401
    except Exception:
        pass

    prd_spec = parse_with_type_hint(prd_path_hint)
    if prd_spec:
        print(f"  ✓ Parsed {len(prd_spec.endpoints)} endpoints from PRD (confidence={prd_spec.confidence:.2f})")
    else:
        print("  ⚠ No PRD endpoints parsed; proceeding with OpenAPI-only tests")

    # Merge specs (OpenAPI primary, PRD endpoints appended)
    merged = UnifiedAPISpec(
        source_type=SourceType.OPENAPI,
        source_path=str(openapi_path),
        metadata=openapi_spec.metadata,
        endpoints=list(openapi_spec.endpoints),
        schemas=openapi_spec.schemas or {},
        confidence=openapi_spec.confidence,
    )

    if prd_spec and prd_spec.endpoints:
        # Merge PRD endpoints: allow PRD to override OpenAPI definitions when
        # they share the same method:path (this lets PRD-driven expectations
        # surface as drift when the implementation differs).
        existing_map = {ep.endpoint_id: i for i, ep in enumerate(merged.endpoints)}
        for ep in prd_spec.endpoints:
            if ep.endpoint_id in existing_map:
                idx = existing_map[ep.endpoint_id]
                merged.endpoints[idx] = ep
            else:
                merged.endpoints.append(ep)

    print(f"Generating tests from merged spec ({len(merged.endpoints)} endpoints)...")
    gen_config = TestGenerationConfig()
    generator = MasterTestGenerator(gen_config)
    test_suite = generator.generate_test_suite(merged)
    print(f"  ✓ Generated {len(test_suite.test_cases)} test cases")

    print("Executing tests against:", api_url)
    exec_cfg = ExecutionConfig(parallel_workers=4, timeout_seconds=10)
    executor = TestExecutor(api_url, exec_cfg)
    results = executor.execute_tests_sync(test_suite.test_cases)

    collector = ResultCollector()
    collector.add_results(results)
    summary = collector.get_summary()

    print("\nExecution summary:")
    print(f"  Total: {summary.total}")
    print(f"  Passed: {summary.passed}")
    print(f"  Failed: {summary.failed}")

    print("\nExecution summary:")
    print(f"  Total: {summary.total}")
    print(f"  Passed: {summary.passed}")
    print(f"  Failed: {summary.failed}")

    # Step: Extract contract from merged spec
    print("\nExtracting contract rules from merged spec...")
    extractor = ConstraintExtractor(merged)
    api_contract = extractor.extract_contract()
    try:
        contracts_count = len(api_contract.endpoint_contracts)
    except Exception:
        contracts_count = getattr(api_contract, 'endpoints', len(merged.endpoints))
    print(f"  ✓ Extracted contracts for {contracts_count} endpoints")

    # Prepare config for reporting and drift detection
    cfg = Config()
    cfg.reporting.output_directory = Path("demo/test_demo/reports")
    cfg.reporting.generate_claude_integration = True

    # Step: Detect drift
    print("Detecting drift...")
    # Use config's drift_detection settings
    drift_detector = DriftDetector(api_contract, cfg.drift_detection)
    drift_report = drift_detector.detect_drift(summary)
    drift_report.api_url = api_url
    print(f"  ✓ Detected {drift_report.summary.total_issues} drift issues")

    # Step: AI analysis (remediation suggestions) - best-effort (requires API key)
    analysis_result = None
    try:
        ai_analyzer = AIAnalyzer(cfg.ai_analysis)
        analysis_result = ai_analyzer.analyze_drift(drift_report)
        if analysis_result:
            print("  ✓ AI analysis produced insights (may be empty without API key)")
    except Exception as e:
        print(f"  ⚠ AI analysis skipped/failed: {e}")

    # Step: Generate reports and remediation skills
    print("Generating reports and remediation files...")
    report_generator = ReportGenerator(cfg)
    output_dir = cfg.reporting.output_directory
    output_dir.mkdir(parents=True, exist_ok=True)
    report_paths = report_generator.generate_reports(
        drift_report=drift_report,
        analysis_result=analysis_result,
        output_format="all",
        output_dir=output_dir,
        spec_path=openapi_path,
    )

    print("Reports generated:")
    for k, p in report_paths.items():
        print(f"  - {k}: {p}")

    # Final exit
    if drift_report.has_critical_issues():
        print("Critical issues found — review remediation files in .acv/")
        raise SystemExit(3)
    elif drift_report.has_issues():
        print("Drift issues detected — remediation files generated (if applicable)")
        raise SystemExit(0)
    else:
        print("No drift detected")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
