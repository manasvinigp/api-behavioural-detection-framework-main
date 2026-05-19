#!/usr/bin/env python3
"""
API Behavioral Drift Detection - Comprehensive Demo Runner

This script provides multiple demo scenarios for the drift detection framework.
Supports mock APIs, real microservices, and custom APIs.

Usage:
    # Quick mock demo
    python run_demo.py --target sample_demo

    # Real microservices demo
    python run_demo.py --mode real --spec specs/api.yaml --base-url http://localhost:8080 --target microservices_demo

    # With ML features
    python run_demo.py --enable-ml --target sample_demo

    # With AI analysis
    export ANTHROPIC_API_KEY="sk-ant-..."
    python run_demo.py --enable-ai --target sample_demo
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from api_contract_validator.config.logging import LoggerSetup, get_logger
from api_contract_validator.config.models import (
    ExecutionConfig,
    TestGenerationConfig,
    DriftDetectionConfig,
    LoggingConfig,
    ReportingConfig,
    AIAnalysisConfig,
)
from api_contract_validator.input.openapi.parser import OpenAPIParser
from api_contract_validator.schema.contract.builder import ContractBuilder
from api_contract_validator.generation.test_generator import MasterTestGenerator
from api_contract_validator.execution.runner.executor import TestExecutor
from api_contract_validator.analysis.drift.detector import MultiDimensionalDriftDetector
from api_contract_validator.analysis.reasoning.patterns import PatternMatcher
from api_contract_validator.reporting.cli.summary import CLIReporter
from api_contract_validator.reporting.markdown.generator import MarkdownReportGenerator
from api_contract_validator.reporting.json.generator import JSONReportGenerator

logger = get_logger("demo")


def create_mock_api_spec() -> Dict[str, Any]:
    """Create a sample OpenAPI spec for mock demo."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample User API",
            "version": "1.0.0",
            "description": "Demo API for drift detection testing"
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


def setup_demo_environment(target_dir: Path) -> None:
    """Create directory structure for demo results."""
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "results").mkdir(exist_ok=True)
    (target_dir / "results" / "test_results").mkdir(exist_ok=True)
    (target_dir / "results" / "progressive_drift").mkdir(exist_ok=True)
    (target_dir / "config").mkdir(exist_ok=True)
    (target_dir / "logs").mkdir(exist_ok=True)

    logger.info(f"Demo environment set up at: {target_dir}")


def run_demo(args):
    """Run the complete drift detection demo."""

    # Setup
    target_dir = Path(args.target)
    setup_demo_environment(target_dir)

    # Configure logging using LoggerSetup
    log_file = target_dir / "logs" / "demo.log"
    logger_cfg = LoggingConfig(level=logging.INFO, file_path=str(log_file))
    LoggerSetup.setup(logger_cfg)

    logger.info("=" * 80)
    logger.info("API BEHAVIORAL DRIFT DETECTION - DEMO")
    logger.info("=" * 80)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Target: {args.target}")

    # Load or create OpenAPI spec
    if args.mode == "mock":
        logger.info("Creating mock API specification...")
        spec_dict = create_mock_api_spec()

        # Save spec to target directory
        spec_file = target_dir / "config" / "api_spec.yaml"
        import yaml
        with open(spec_file, 'w') as f:
            yaml.dump(spec_dict, f)

        # Parse spec
        parser = OpenAPIParser()
        unified_spec = parser.parse_dict(spec_dict)

        # Mock API URL
        base_url = "http://localhost:8000"
        logger.warning("Mock mode: Using simulated responses (no real API calls)")

    else:  # real mode
        if not args.spec:
            logger.error("--spec is required for real mode")
            return 1

        spec_path = Path(args.spec)
        if not spec_path.exists():
            logger.error(f"Spec file not found: {spec_path}")
            return 1

        logger.info(f"Parsing OpenAPI spec: {spec_path}")
        parser = OpenAPIParser()
        unified_spec = parser.parse_file(spec_path)

        base_url = args.base_url or "http://localhost:8080"

    logger.info(f"API Base URL: {base_url}")
    logger.info(f"Endpoints found: {len(unified_spec.endpoints)}")

    # Build contract
    logger.info("Building API contract model...")
    contract_builder = ContractBuilder()
    contract = contract_builder.merge(unified_spec, {})

    # Generate tests
    logger.info("Generating test suite...")
    test_config = TestGenerationConfig(
        generate_valid=True,
        generate_invalid=True,
        generate_boundary=True,
        max_tests_per_endpoint=20,
        enable_prioritization=True
    )

    test_generator = MasterTestGenerator(test_config)
    test_suite = test_generator.generate_from_contract(contract)

    logger.info(f"Generated {len(test_suite.test_cases)} test cases")

    # Execute tests
    if args.mode == "mock":
        logger.info("Mock mode: Simulating test execution...")
        # In mock mode, create simulated results
        from api_contract_validator.execution.runner.models import TestExecutionResult, ExecutionStatus

        results = []
        for i, test in enumerate(test_suite.test_cases[:10]):  # Limit for demo
            # Simulate some passing, some failing
            status = ExecutionStatus.PASSED if i % 3 != 0 else ExecutionStatus.FAILED

            result = TestExecutionResult(
                test_id=test.test_id,
                endpoint_id=test.endpoint.path,
                status=status,
                request={"method": test.method.value, "path": test.path},
                response={"status_code": 200 if status == ExecutionStatus.PASSED else 400},
                response_time_ms=50.0 + (i * 10),
                assertions=[],
                error_message="Simulated failure" if status == ExecutionStatus.FAILED else None
            )
            results.append(result)

        logger.info(f"Simulated execution of {len(results)} tests")
    else:
        logger.info(f"Executing tests against {base_url}...")
        exec_config = ExecutionConfig(
            parallel_workers=5,
            timeout_seconds=10,
            retry_attempts=2
        )

        executor = TestExecutor(base_url, exec_config)
        results = executor.execute_tests_sync(test_suite.test_cases)

        logger.info(f"Executed {len(results)} tests")

    # Detect drift
    logger.info("Analyzing drift...")
    drift_config = DriftDetectionConfig(
        detect_contract_drift=True,
        detect_validation_drift=True,
        detect_behavioral_drift=args.enable_ml,
    )

    drift_detector = MultiDimensionalDriftDetector(contract, drift_config)
    drift_report = drift_detector.analyze_results(results)

    logger.info(f"Drift analysis complete. Overall score: {drift_report.overall_drift_score:.2f}")

    # Root cause analysis
    if drift_report.has_issues():
        logger.info("Running root cause analysis...")
        pattern_matcher = PatternMatcher()
        root_causes = pattern_matcher.analyze_drift_issues(
            drift_report.issues,
            drift_report.contract_drift,
            drift_report.validation_drift,
            drift_report.behavioral_drift
        )

        remediations = pattern_matcher.generate_remediations(root_causes)

        logger.info(f"Found {len(root_causes)} root cause patterns")
        logger.info(f"Generated {len(remediations)} remediation suggestions")

        # Save root cause analysis
        rca_file = target_dir / "results" / "root_cause_analysis.json"
        with open(rca_file, 'w') as f:
            rca_data = {
                "root_causes": [
                    {
                        "pattern": rc.issue_id,
                        "endpoint": rc.endpoint_id,
                        "hypothesis": rc.hypothesis,
                        "confidence": rc.confidence.value,
                        "evidence": rc.evidence_references
                    }
                    for rc in root_causes
                ],
                "remediations": [
                    {
                        "title": rem.title,
                        "description": rem.description,
                        "code_example": rem.code_example,
                        "effort": rem.estimated_effort,
                        "priority": rem.priority
                    }
                    for rem in remediations
                ]
            }
            json.dump(rca_data, f, indent=2)

        logger.info(f"Root cause analysis saved to: {rca_file}")

    # Generate reports
    logger.info("Generating reports...")

    # CLI summary
    cli_reporter = CLIReporter()
    cli_reporter.print_summary(drift_report)

    # Markdown report
    md_file = target_dir / "results" / "drift_report.md"
    md_generator = MarkdownReportGenerator(output_path=md_file)
    md_generator.generate(drift_report, results)
    logger.info(f"Markdown report: {md_file}")

    # JSON report
    json_file = target_dir / "results" / "drift_report.json"
    json_generator = JSONReportGenerator(output_path=json_file)
    json_generator.generate(drift_report, results)
    logger.info(f"JSON report: {json_file}")

    # Summary
    logger.info("=" * 80)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Results available at: {target_dir / 'results'}")
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"  1. View report: cat {md_file}")
    logger.info(f"  2. Check JSON: cat {json_file} | python -m json.tool")
    logger.info(f"  3. Review logs: cat {log_file}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="API Behavioral Drift Detection Framework - Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick mock demo
  python run_demo.py --target sample_demo

  # Real microservices demo
  python run_demo.py --mode real --spec specs/api.yaml --base-url http://localhost:3550 --target microservices_demo

  # With ML features
  python run_demo.py --enable-ml --target sample_demo

  # With AI analysis
  export ANTHROPIC_API_KEY="sk-ant-..."
  python run_demo.py --enable-ai --target sample_demo
        """
    )

    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        default="mock",
        help="Demo mode: mock (simulated) or real (actual API calls)"
    )

    parser.add_argument(
        "--spec",
        type=str,
        help="Path to OpenAPI specification file (required for real mode)"
    )

    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL of API to test (required for real mode)"
    )

    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target directory for demo results (e.g., 'sample_demo')"
    )

    parser.add_argument(
        "--enable-ml",
        action="store_true",
        help="Enable ML-based behavioral drift detection (requires sentence-transformers)"
    )

    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help="Enable AI-powered root cause analysis (requires ANTHROPIC_API_KEY)"
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing progressive drift history"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.mode == "real" and not args.spec:
        parser.error("--spec is required when --mode=real")

    try:
        return run_demo(args)
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Demo failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
