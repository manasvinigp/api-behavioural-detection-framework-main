"""
Pattern-Based Root Cause Analysis

Deterministic pattern matching for common API drift causes.
Complements AI-based analysis with explainable, rule-based hypotheses.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from api_contract_validator.analysis.drift.models import (
    ContractDrift,
    ValidationDrift,
    BehavioralDrift,
    DriftIssue,
)
from api_contract_validator.analysis.reasoning.models import (
    RootCauseAnalysis,
    RemediationSuggestion,
    AnalysisConfidence,
)


class DriftPattern(Enum):
    """Common API drift patterns."""

    # Contract drift patterns
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNEXPECTED_FIELD = "unexpected_field"
    TYPE_MISMATCH = "type_mismatch"
    SCHEMA_EVOLUTION = "schema_evolution"

    # Validation drift patterns
    MISSING_INPUT_VALIDATION = "missing_input_validation"
    PERMISSIVE_VALIDATION = "permissive_validation"
    INCOMPLETE_ERROR_HANDLING = "incomplete_error_handling"

    # Behavioral drift patterns
    RESPONSE_INCONSISTENCY = "response_inconsistency"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    NONDETERMINISTIC_BEHAVIOR = "nondeterministic_behavior"

    # Cross-cutting patterns
    DATABASE_MIGRATION_ISSUE = "database_migration_issue"
    MIDDLEWARE_CHANGE = "middleware_change"
    SERIALIZER_UPDATE = "serializer_update"


@dataclass
class PatternMatch:
    """A matched drift pattern with confidence."""

    pattern: DriftPattern
    confidence: float  # 0.0 - 1.0
    evidence: List[str]
    affected_endpoints: List[str]
    affected_fields: List[str]


class PatternMatcher:
    """
    Pattern-based root cause detector.

    Uses deterministic rules to identify common drift patterns.
    """

    def __init__(self):
        self.pattern_rules = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[DriftPattern, Dict[str, Any]]:
        """Initialize pattern detection rules."""
        return {
            DriftPattern.MISSING_REQUIRED_FIELD: {
                "check": self._check_missing_required_field,
                "hypothesis_template": "Required field '{field}' is missing from API response. The field is defined in the specification but never returned by the API implementation.",
                "why_template": "The API implementation likely forgot to include the field in the response serializer or database query projection.",
                "fix_template": "Add field '{field}' to the response serializer/model in endpoint '{endpoint}'.",
                "code_example_template": """# Example fix (Python/FastAPI):
class UserResponse(BaseModel):
    id: int
    name: str
    {field}: {type}  # Add this field

@app.get("/users/{{user_id}}")
def get_user(user_id: int) -> UserResponse:
    user = db.get_user(user_id)
    return UserResponse(
        id=user.id,
        name=user.name,
        {field}=user.{field}  # Include the field
    )
""",
            },
            DriftPattern.UNEXPECTED_FIELD: {
                "check": self._check_unexpected_field,
                "hypothesis_template": "Response contains unexpected field '{field}' not defined in specification. This may be a new field added without updating the contract.",
                "why_template": "Developer added field to response without updating OpenAPI spec, or field is leaked from internal implementation.",
                "fix_template": "Either add '{field}' to OpenAPI spec if intended, or remove from response if it's an implementation detail.",
                "code_example_template": """# Option 1: Update OpenAPI spec to include field
# Option 2: Exclude field from serializer:
class UserResponse(BaseModel):
    id: int
    name: str
    # Don't include: {field}

    class Config:
        # Or use field exclusion
        fields = {{'internal_field': {{'exclude': True}}}}
""",
            },
            DriftPattern.TYPE_MISMATCH: {
                "check": self._check_type_mismatch,
                "hypothesis_template": "Field '{field}' has type mismatch. Expected {expected_type} but got {actual_type}.",
                "why_template": "Type coercion issue in serializer, database schema change, or incorrect type casting in business logic.",
                "fix_template": "Ensure field '{field}' is properly typed in the serializer and matches the specification.",
                "code_example_template": """# Fix type conversion:
class UserResponse(BaseModel):
    id: int
    age: int  # Ensure correct type

@app.get("/users/{{user_id}}")
def get_user(user_id: int) -> UserResponse:
    user = db.get_user(user_id)
    return UserResponse(
        id=user.id,
        age=int(user.age)  # Explicit type conversion
    )
""",
            },
            DriftPattern.MISSING_INPUT_VALIDATION: {
                "check": self._check_missing_validation,
                "hypothesis_template": "Endpoint '{endpoint}' accepts invalid input that should be rejected. Missing validation for constraint: {constraint}.",
                "why_template": "Validation middleware not applied, or validator configuration incomplete. API accepts data it shouldn't.",
                "fix_template": "Add input validation for field '{field}' in endpoint '{endpoint}'.",
                "code_example_template": """# Add validation (Pydantic example):
from pydantic import BaseModel, Field, validator

class UserInput(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\\.[^@]+$')
    age: int = Field(..., ge=0, le=150)

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v
""",
            },
            DriftPattern.SCHEMA_EVOLUTION: {
                "check": self._check_schema_evolution,
                "hypothesis_template": "Multiple fields changed across {count} endpoints. Likely schema evolution or database migration.",
                "why_template": "Recent database schema change, model refactoring, or API version update without proper migration.",
                "fix_template": "Update OpenAPI specification to match current schema, or add API versioning.",
                "code_example_template": """# Option 1: Update spec to current schema
# Option 2: Add API versioning:
@app.get("/v2/users/{{user_id}}")  # New version
def get_user_v2(user_id: int) -> UserResponseV2:
    # Updated schema
    pass

@app.get("/v1/users/{{user_id}}")  # Legacy support
def get_user_v1(user_id: int) -> UserResponseV1:
    # Old schema for backwards compatibility
    pass
""",
            },
        }

    def analyze_drift_issues(
        self,
        drift_issues: List[DriftIssue],
        contract_drift: Optional[ContractDrift] = None,
        validation_drift: Optional[ValidationDrift] = None,
        behavioral_drift: Optional[BehavioralDrift] = None,
    ) -> List[RootCauseAnalysis]:
        """
        Analyze drift issues and generate root cause hypotheses.

        Args:
            drift_issues: List of detected drift issues
            contract_drift: Contract drift details
            validation_drift: Validation drift details
            behavioral_drift: Behavioral drift details

        Returns:
            List of root cause analyses with confidence scores
        """
        root_causes = []

        # Match patterns against drift data
        matches = self._find_pattern_matches(
            drift_issues, contract_drift, validation_drift, behavioral_drift
        )

        # Generate root cause analysis for each match
        for match in matches:
            root_cause = self._generate_root_cause(match)
            root_causes.append(root_cause)

        # Group related issues
        root_causes = self._group_related_causes(root_causes)

        return root_causes

    def _find_pattern_matches(
        self,
        drift_issues: List[DriftIssue],
        contract_drift: Optional[ContractDrift],
        validation_drift: Optional[ValidationDrift],
        behavioral_drift: Optional[BehavioralDrift],
    ) -> List[PatternMatch]:
        """Find all matching patterns in drift data."""
        matches = []

        for pattern, rule in self.pattern_rules.items():
            check_func = rule["check"]
            match = check_func(drift_issues, contract_drift, validation_drift, behavioral_drift)

            if match:
                matches.append(match)

        return matches

    def _check_missing_required_field(
        self, drift_issues, contract_drift, validation_drift, behavioral_drift
    ) -> Optional[PatternMatch]:
        """Check for missing required field pattern."""
        if not contract_drift:
            return None

        evidence = []
        affected_endpoints = []
        affected_fields = []

        # Look for missing required fields in contract violations
        for issue in drift_issues:
            if "missing" in issue.description.lower() and "required" in issue.description.lower():
                evidence.append(issue.description)
                affected_endpoints.append(issue.endpoint_id)

                # Extract field name from description
                import re
                field_match = re.search(r"field[:\s]+['\"]?(\w+)['\"]?", issue.description, re.IGNORECASE)
                if field_match:
                    affected_fields.append(field_match.group(1))

        if evidence:
            return PatternMatch(
                pattern=DriftPattern.MISSING_REQUIRED_FIELD,
                confidence=0.9,  # High confidence for explicit missing fields
                evidence=evidence,
                affected_endpoints=list(set(affected_endpoints)),
                affected_fields=list(set(affected_fields)),
            )

        return None

    def _check_unexpected_field(
        self, drift_issues, contract_drift, validation_drift, behavioral_drift
    ) -> Optional[PatternMatch]:
        """Check for unexpected field pattern."""
        if not contract_drift:
            return None

        evidence = []
        affected_endpoints = []
        affected_fields = []

        for issue in drift_issues:
            if "unexpected" in issue.description.lower() or "extra" in issue.description.lower():
                evidence.append(issue.description)
                affected_endpoints.append(issue.endpoint_id)

                # Extract field name
                import re
                field_match = re.search(r"field[:\s]+['\"]?(\w+)['\"]?", issue.description, re.IGNORECASE)
                if field_match:
                    affected_fields.append(field_match.group(1))

        if evidence:
            return PatternMatch(
                pattern=DriftPattern.UNEXPECTED_FIELD,
                confidence=0.85,
                evidence=evidence,
                affected_endpoints=list(set(affected_endpoints)),
                affected_fields=list(set(affected_fields)),
            )

        return None

    def _check_type_mismatch(
        self, drift_issues, contract_drift, validation_drift, behavioral_drift
    ) -> Optional[PatternMatch]:
        """Check for type mismatch pattern."""
        evidence = []
        affected_endpoints = []
        affected_fields = []

        for issue in drift_issues:
            if "type" in issue.description.lower() and ("mismatch" in issue.description.lower() or "expected" in issue.description.lower()):
                evidence.append(issue.description)
                affected_endpoints.append(issue.endpoint_id)

                import re
                field_match = re.search(r"field[:\s]+['\"]?(\w+)['\"]?", issue.description, re.IGNORECASE)
                if field_match:
                    affected_fields.append(field_match.group(1))

        if evidence:
            return PatternMatch(
                pattern=DriftPattern.TYPE_MISMATCH,
                confidence=0.90,
                evidence=evidence,
                affected_endpoints=list(set(affected_endpoints)),
                affected_fields=list(set(affected_fields)),
            )

        return None

    def _check_missing_validation(
        self, drift_issues, contract_drift, validation_drift, behavioral_drift
    ) -> Optional[PatternMatch]:
        """Check for missing validation pattern."""
        if not validation_drift:
            return None

        evidence = []
        affected_endpoints = []

        for issue in drift_issues:
            if "validation" in issue.description.lower() or "accepted invalid" in issue.description.lower():
                evidence.append(issue.description)
                affected_endpoints.append(issue.endpoint_id)

        if evidence:
            return PatternMatch(
                pattern=DriftPattern.MISSING_INPUT_VALIDATION,
                confidence=0.88,
                evidence=evidence,
                affected_endpoints=list(set(affected_endpoints)),
                affected_fields=[],
            )

        return None

    def _check_schema_evolution(
        self, drift_issues, contract_drift, validation_drift, behavioral_drift
    ) -> Optional[PatternMatch]:
        """Check for schema evolution pattern (multiple related changes)."""
        # If multiple fields are affected across endpoints, might be schema evolution
        affected_endpoints = set()
        affected_fields = set()

        for issue in drift_issues:
            affected_endpoints.add(issue.endpoint_id)

            import re
            field_match = re.search(r"field[:\s]+['\"]?(\w+)['\"]?", issue.description, re.IGNORECASE)
            if field_match:
                affected_fields.add(field_match.group(1))

        # Schema evolution if >= 3 fields or >= 2 endpoints affected
        if len(affected_fields) >= 3 or len(affected_endpoints) >= 2:
            return PatternMatch(
                pattern=DriftPattern.SCHEMA_EVOLUTION,
                confidence=0.70,  # Medium confidence, could be coincidence
                evidence=[f"{len(affected_fields)} fields changed across {len(affected_endpoints)} endpoints"],
                affected_endpoints=list(affected_endpoints),
                affected_fields=list(affected_fields),
            )

        return None

    def _generate_root_cause(self, match: PatternMatch) -> RootCauseAnalysis:
        """Generate root cause analysis from pattern match."""
        rule = self.pattern_rules[match.pattern]

        # Generate hypothesis with field/endpoint substitution
        hypothesis = rule["hypothesis_template"]
        if match.affected_fields:
            hypothesis = hypothesis.replace("{field}", match.affected_fields[0])
        if match.affected_endpoints:
            hypothesis = hypothesis.replace("{endpoint}", match.affected_endpoints[0])
        hypothesis = hypothesis.replace("{count}", str(len(match.affected_endpoints)))

        # Map confidence float to enum
        if match.confidence >= 0.85:
            confidence = AnalysisConfidence.HIGH
        elif match.confidence >= 0.65:
            confidence = AnalysisConfidence.MEDIUM
        else:
            confidence = AnalysisConfidence.LOW

        return RootCauseAnalysis(
            issue_id=match.pattern.value,
            endpoint_id=match.affected_endpoints[0] if match.affected_endpoints else "multiple",
            hypothesis=hypothesis,
            contributing_factors=[rule["why_template"]],
            confidence=confidence,
            evidence_references=match.evidence[:5],  # Limit to 5 evidence items
        )

    def _group_related_causes(
        self, root_causes: List[RootCauseAnalysis]
    ) -> List[RootCauseAnalysis]:
        """Group related root causes to avoid duplication."""
        # Simple grouping by endpoint_id
        grouped = {}

        for rc in root_causes:
            key = (rc.endpoint_id, rc.issue_id)
            if key not in grouped:
                grouped[key] = rc
            else:
                # Merge evidence
                grouped[key].evidence_references.extend(rc.evidence_references)
                grouped[key].evidence_references = list(set(grouped[key].evidence_references))

        return list(grouped.values())

    def generate_remediations(
        self, root_causes: List[RootCauseAnalysis]
    ) -> List[RemediationSuggestion]:
        """Generate remediation suggestions from root causes."""
        remediations = []

        for rc in root_causes:
            # Find matching pattern
            pattern = DriftPattern(rc.issue_id) if rc.issue_id in [p.value for p in DriftPattern] else None

            if not pattern:
                continue

            rule = self.pattern_rules.get(pattern)
            if not rule:
                continue

            # Extract field name from hypothesis for template substitution
            import re
            field_match = re.search(r"field[:\s]+['\"]?(\w+)['\"]?", rc.hypothesis, re.IGNORECASE)
            field_name = field_match.group(1) if field_match else "field_name"

            # Generate remediation
            fix_desc = rule["fix_template"].replace("{field}", field_name).replace("{endpoint}", rc.endpoint_id)
            code_example = rule["code_example_template"].replace("{field}", field_name).replace("{type}", "str")

            remediation = RemediationSuggestion(
                issue_id=rc.issue_id,
                endpoint_id=rc.endpoint_id,
                title=f"Fix {pattern.value.replace('_', ' ').title()}",
                description=fix_desc,
                code_example=code_example,
                implementation_steps=[
                    "1. Identify the serializer/model for this endpoint",
                    "2. Add or update the field definition",
                    "3. Update tests to verify the fix",
                    "4. Update OpenAPI specification if needed",
                ],
                estimated_effort="low" if rc.confidence == AnalysisConfidence.HIGH else "medium",
                priority="high" if rc.confidence == AnalysisConfidence.HIGH else "medium",
            )

            remediations.append(remediation)

        return remediations
