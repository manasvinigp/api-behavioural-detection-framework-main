"""
Behavioral Drift Detector

Detects logical inconsistencies and unexpected behavior patterns in API responses.
"""

from collections import defaultdict
from typing import Any, Dict, List, Set

from api_contract_validator.analysis.drift.models import (
    BehavioralDriftIssue,
    DriftSeverity,
)
from api_contract_validator.config.logging import get_logger
from api_contract_validator.execution.collector.result_collector import ExecutionSummary

logger = get_logger("api_contract_validator.analyzer")


class BehavioralDriftDetector:
    """
    Detects behavioral drift by analyzing response patterns and
    identifying inconsistencies.
    """

    def detect(self, execution_summary: ExecutionSummary) -> List[BehavioralDriftIssue]:
        """
        Detect behavioral drift from test execution results.

        Behavioral drift includes:
        - Connection failures (API unavailable/unreachable)
        - Inconsistent responses for equivalent tests
        - Unexpected null values
        - Extra/missing fields across responses
        - Response structure anomalies
        - Server errors (5xx) indicating API reliability issues

        Args:
            execution_summary: Test execution results

        Returns:
            List of behavioral drift issues
        """
        logger.info("Starting behavioral drift detection")
        drift_issues: List[BehavioralDriftIssue] = []

        # FIRST: Detect connection failures (tests with errors but no status_code)
        connection_failure_issues = self._detect_connection_failures(execution_summary)
        drift_issues.extend(connection_failure_issues)

        # SECOND: Detect 5xx server errors (critical reliability issue)
        server_error_issues = self._detect_server_errors(execution_summary)
        drift_issues.extend(server_error_issues)

        # Group responses by endpoint AND status code class for comparison
        # FIXED: Only compare responses with same status code class (2xx vs 4xx vs 5xx)
        # This avoids false positives when comparing success vs error responses
        endpoint_responses: Dict[str, Dict[str, List]] = defaultdict(lambda: defaultdict(list))
        for result in execution_summary.results:
            if result.passed and result.response_body and result.status_code:
                endpoint_id = result.test_case.endpoint.endpoint_id
                # Group by status code class: 2xx, 4xx, 5xx
                status_class = f"{result.status_code // 100}xx"
                endpoint_responses[endpoint_id][status_class].append(result)

        # Analyze each endpoint's response patterns (within same status class)
        for endpoint_id, status_groups in endpoint_responses.items():
            for status_class, results in status_groups.items():
                if len(results) < 2:
                    continue  # Need multiple responses to detect inconsistencies

                # Detect null value anomalies
                null_issues = self._detect_unexpected_nulls(endpoint_id, results, status_class)
                drift_issues.extend(null_issues)

                # Detect field presence inconsistencies
                field_issues = self._detect_field_inconsistencies(endpoint_id, results, status_class)
                drift_issues.extend(field_issues)

                # Detect response structure variations
                structure_issues = self._detect_structure_variations(endpoint_id, results, status_class)
                drift_issues.extend(structure_issues)

        logger.info(f"Behavioral drift detection complete: {len(drift_issues)} issues found")
        return drift_issues

    def _detect_connection_failures(self, execution_summary: ExecutionSummary) -> List[BehavioralDriftIssue]:
        """
        Detect connection failures where tests failed but no HTTP status code was received.

        This indicates:
        - API is unreachable (connection refused)
        - Network timeouts
        - DNS resolution failures
        - API server is down

        These are CRITICAL issues as the API is unavailable.
        """
        issues = []

        # Group connection failures by endpoint
        endpoint_failures: Dict[str, List] = defaultdict(list)
        for result in execution_summary.results:
            # Check for failed tests with no status code (connection-level failure)
            if not result.passed and result.status_code is None and result.error:
                endpoint_id = result.test_case.endpoint.endpoint_id
                endpoint_failures[endpoint_id].append(result)

        # Create issue for each affected endpoint
        for endpoint_id, failure_results in endpoint_failures.items():
            total_tests_for_endpoint = sum(
                1 for r in execution_summary.results
                if r.test_case.endpoint.endpoint_id == endpoint_id
            )
            failure_count = len(failure_results)
            failure_rate = (failure_count / total_tests_for_endpoint) * 100

            # Collect error types
            error_types = defaultdict(int)
            for result in failure_results:
                # Categorize error type
                error_lower = result.error.lower()
                if 'timeout' in error_lower:
                    error_types['timeout'] += 1
                elif 'connection' in error_lower or 'refused' in error_lower:
                    error_types['connection_refused'] += 1
                elif 'dns' in error_lower or 'resolve' in error_lower:
                    error_types['dns_failure'] += 1
                else:
                    error_types['other'] += 1

            issue = BehavioralDriftIssue(
                endpoint_id=endpoint_id,
                test_ids=[r.test_case.test_id for r in failure_results],
                anomaly_type="connection_failures",
                description=(
                    f"Endpoint is unreachable: {failure_count} tests failed with connection errors "
                    f"out of {total_tests_for_endpoint} tests ({failure_rate:.1f}% failure rate). "
                    f"Error types: {dict(error_types)}"
                ),
                evidence={
                    "failure_count": failure_count,
                    "total_tests": total_tests_for_endpoint,
                    "failure_rate_percent": round(failure_rate, 2),
                    "error_types": dict(error_types),
                    "sample_errors": [
                        {
                            "test_id": r.test_case.test_id,
                            "error": r.error,
                            "test_type": r.test_case.test_type.value,
                        }
                        for r in failure_results[:5]  # Show first 5 examples
                    ],
                },
                severity=DriftSeverity.CRITICAL,  # API unreachable is always CRITICAL
            )
            issues.append(issue)

        return issues

    def _detect_server_errors(self, execution_summary: ExecutionSummary) -> List[BehavioralDriftIssue]:
        """
        Detect 5xx server errors indicating API reliability/availability issues.

        5xx errors are critical as they indicate:
        - API implementation bugs
        - Infrastructure failures
        - Unhandled exceptions
        """
        issues = []

        # Group 5xx errors by endpoint
        endpoint_errors: Dict[str, List] = defaultdict(list)
        for result in execution_summary.results:
            # FIXED: Add null check before comparison
            if result.status_code is not None and 500 <= result.status_code < 600:
                endpoint_id = result.test_case.endpoint.endpoint_id
                endpoint_errors[endpoint_id].append(result)

        # Create issue for each affected endpoint
        for endpoint_id, error_results in endpoint_errors.items():
            total_tests_for_endpoint = sum(
                1 for r in execution_summary.results
                if r.test_case.endpoint.endpoint_id == endpoint_id
            )
            error_count = len(error_results)
            error_rate = (error_count / total_tests_for_endpoint) * 100

            # Collect status code distribution
            status_codes = defaultdict(int)
            for result in error_results:
                status_codes[result.status_code] += 1

            issue = BehavioralDriftIssue(
                endpoint_id=endpoint_id,
                test_ids=[r.test_case.test_id for r in error_results],
                anomaly_type="server_errors",
                description=(
                    f"Endpoint returned {error_count} server errors (5xx) out of "
                    f"{total_tests_for_endpoint} tests ({error_rate:.1f}% error rate). "
                    f"Status codes: {dict(status_codes)}"
                ),
                evidence={
                    "error_count": error_count,
                    "total_tests": total_tests_for_endpoint,
                    "error_rate_percent": round(error_rate, 2),
                    "status_code_distribution": dict(status_codes),
                    "sample_responses": [
                        {
                            "test_id": r.test_case.test_id,
                            "status_code": r.status_code,
                            "test_type": r.test_case.test_type.value,
                        }
                        for r in error_results[:5]  # Show first 5 examples
                    ],
                },
                severity=DriftSeverity.CRITICAL if error_rate > 50 else DriftSeverity.HIGH,
            )
            issues.append(issue)

        return issues

    def _detect_unexpected_nulls(self, endpoint_id: str, results: List, status_class: str) -> List[BehavioralDriftIssue]:
        """Detect fields that are sometimes null when they shouldn't be."""
        issues = []
        field_null_status: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"null": 0, "non_null": 0}
        )

        # Track null/non-null occurrences for each field
        for result in results:
            self._track_null_status(result.response_body, "", field_null_status)

        # Find fields that are inconsistently null
        for field_path, status in field_null_status.items():
            null_count = status["null"]
            non_null_count = status["non_null"]
            total = null_count + non_null_count

            # If field is null in some responses but not others, flag it
            if null_count > 0 and non_null_count > 0:
                null_percentage = (null_count / total) * 100

                issue = BehavioralDriftIssue(
                    endpoint_id=endpoint_id,
                    test_ids=[r.test_case.test_id for r in results],
                    anomaly_type="inconsistent_null_values",
                    description=(
                        f"Field '{field_path}' is null in {null_percentage:.1f}% of {status_class} responses "
                        f"({null_count}/{total}), indicating inconsistent behavior"
                    ),
                    evidence={
                        "field_path": field_path,
                        "null_count": null_count,
                        "non_null_count": non_null_count,
                        "null_percentage": null_percentage,
                        "status_class": status_class,
                    },
                    severity=DriftSeverity.MEDIUM if null_percentage > 30 else DriftSeverity.LOW,
                )
                issues.append(issue)

        return issues

    def _detect_field_inconsistencies(
        self, endpoint_id: str, results: List, status_class: str
    ) -> List[BehavioralDriftIssue]:
        """Detect fields that appear in some responses but not others."""
        issues = []

        # Collect all fields seen across responses
        all_fields: Dict[str, int] = defaultdict(int)
        for result in results:
            fields = self._get_all_field_paths(result.response_body, "")
            for field in fields:
                all_fields[field] += 1

        total_responses = len(results)

        # Find fields that don't appear in all responses
        for field_path, count in all_fields.items():
            if 0 < count < total_responses:
                presence_percentage = (count / total_responses) * 100

                issue = BehavioralDriftIssue(
                    endpoint_id=endpoint_id,
                    test_ids=[r.test_case.test_id for r in results],
                    anomaly_type="inconsistent_field_presence",
                    description=(
                        f"Field '{field_path}' appears in only {presence_percentage:.1f}% "
                        f"of {status_class} responses ({count}/{total_responses})"
                    ),
                    evidence={
                        "field_path": field_path,
                        "present_count": count,
                        "total_responses": total_responses,
                        "presence_percentage": presence_percentage,
                        "status_class": status_class,
                    },
                    severity=DriftSeverity.LOW,
                )
                issues.append(issue)

        return issues

    def _detect_structure_variations(
        self, endpoint_id: str, results: List, status_class: str
    ) -> List[BehavioralDriftIssue]:
        """Detect variations in response structure."""
        issues = []

        if len(results) < 2:
            return issues

        # Compare structure types across responses
        structure_signatures = []
        for result in results:
            signature = self._get_structure_signature(result.response_body)
            structure_signatures.append(signature)

        # If all signatures are not identical, there's structural drift
        unique_signatures = set(structure_signatures)
        if len(unique_signatures) > 1:
            issue = BehavioralDriftIssue(
                endpoint_id=endpoint_id,
                test_ids=[r.test_case.test_id for r in results],
                anomaly_type="response_structure_variation",
                description=(
                    f"Response structure varies across {status_class} tests. "
                    f"Found {len(unique_signatures)} different structures in {len(results)} responses"
                ),
                evidence={
                    "unique_structures": len(unique_signatures),
                    "total_responses": len(results),
                    "structures": list(unique_signatures)[:3],  # Show first 3 examples
                    "status_class": status_class,
                },
                severity=DriftSeverity.MEDIUM,
            )
            issues.append(issue)

        return issues

    def _track_null_status(
        self, data: Any, path_prefix: str, field_status: Dict[str, Dict[str, int]]
    ) -> None:
        """Recursively track null status of all fields."""
        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{path_prefix}.{key}" if path_prefix else key
                if value is None:
                    field_status[field_path]["null"] += 1
                else:
                    field_status[field_path]["non_null"] += 1
                    # Recurse into nested structures
                    if isinstance(value, (dict, list)):
                        self._track_null_status(value, field_path, field_status)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._track_null_status(item, f"{path_prefix}[]", field_status)

    def _get_all_field_paths(self, data: Any, path_prefix: str) -> Set[str]:
        """Get all field paths in a data structure."""
        fields = set()

        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{path_prefix}.{key}" if path_prefix else key
                fields.add(field_path)

                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    nested_fields = self._get_all_field_paths(value, field_path)
                    fields.update(nested_fields)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    nested_fields = self._get_all_field_paths(item, f"{path_prefix}[]")
                    fields.update(nested_fields)

        return fields

    def _get_structure_signature(self, data: Any) -> str:
        """Generate a signature representing the structure of the data."""
        if data is None:
            return "null"
        elif isinstance(data, dict):
            if not data:
                return "dict[empty]"
            fields = []
            for key in sorted(data.keys()):
                value_sig = self._get_structure_signature(data[key])
                fields.append(f"{key}:{value_sig}")
            return f"dict[{','.join(fields[:5])}]"  # Limit to 5 fields for readability
        elif isinstance(data, list):
            if not data:
                return "list[empty]"
            item_sig = self._get_structure_signature(data[0])
            return f"list[{item_sig}]"
        elif isinstance(data, bool):
            return "bool"
        elif isinstance(data, int):
            return "int"
        elif isinstance(data, float):
            return "float"
        elif isinstance(data, str):
            return "str"
        else:
            return type(data).__name__
