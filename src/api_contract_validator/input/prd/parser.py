"""
PRD (Product Requirements Document) Parser

Extracts API contract information from semi-structured PRD documents using NLP.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import spacy
from spacy.tokens import Doc

from api_contract_validator.config.exceptions import PRDParsingError
from api_contract_validator.config.logging import get_logger
from api_contract_validator.input.normalizer.models import (
    APIMetadata,
    Endpoint,
    FieldConstraint,
    FieldDefinition,
    FieldType,
    HTTPMethod,
    Parameter,
    RequestBody,
    ResponseBody,
    SourceType,
    UnifiedAPISpec,
)

logger = get_logger(__name__)


class PRDParser:
    """
    Parses PRD documents to extract API specifications using NLP and heuristics.
    """

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise PRDParsingError(
                "spaCy model not found. Run: python -m spacy download en_core_web_sm"
            )

        # Patterns for entity extraction
        self.http_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        self.field_types_map = {
            "string": FieldType.STRING,
            "text": FieldType.STRING,
            "integer": FieldType.INTEGER,
            "int": FieldType.INTEGER,
            "number": FieldType.NUMBER,
            "float": FieldType.NUMBER,
            "boolean": FieldType.BOOLEAN,
            "bool": FieldType.BOOLEAN,
            "array": FieldType.ARRAY,
            "list": FieldType.ARRAY,
            "object": FieldType.OBJECT,
            "dict": FieldType.OBJECT,
        }

    def parse_file(self, prd_path: Path) -> UnifiedAPISpec:
        """
        Parse a PRD document file.

        Args:
            prd_path: Path to PRD document (text, markdown, or docx)

        Returns:
            UnifiedAPISpec instance with confidence scores

        Raises:
            PRDParsingError: If parsing fails
        """
        logger.info(f"Parsing PRD document: {prd_path}")

        try:
            # Read file content
            content = self._read_file(prd_path)

            # Parse with spaCy
            doc = self.nlp(content)

            # Extract components
            metadata = self._extract_metadata(doc, content)
            endpoints = self._extract_endpoints(doc, content)

            # Calculate overall confidence based on extraction quality
            confidence = self._calculate_confidence(endpoints)

            unified_spec = UnifiedAPISpec(
                source_type=SourceType.PRD,
                source_path=str(prd_path),
                metadata=metadata,
                endpoints=endpoints,
                confidence=confidence,
            )

            logger.info(
                f"Extracted {len(endpoints)} endpoints from PRD (confidence: {confidence:.2f})"
            )
            return unified_spec

        except Exception as e:
            raise PRDParsingError(f"Failed to parse PRD document: {e}")

    def _read_file(self, file_path: Path) -> str:
        """Read content from various file formats."""
        suffix = file_path.suffix.lower()

        if suffix in [".txt", ".md", ".markdown"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif suffix == ".docx":
            # Optional: Add python-docx support
            try:
                from docx import Document

                doc = Document(file_path)
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except ImportError:
                raise PRDParsingError(
                    "python-docx required for .docx files. Install with: pip install python-docx"
                )
        else:
            raise PRDParsingError(f"Unsupported file format: {suffix}")

    def _extract_metadata(self, doc: Doc, content: str) -> APIMetadata:
        """Extract API metadata from document."""
        # Extract title (usually first heading or line)
        lines = content.split("\n")
        title = "API from PRD"
        for line in lines[:10]:
            if line.strip() and not line.strip().startswith("#"):
                title = line.strip()
                break

        # Try to extract version
        version_match = re.search(r"version\s*[:=]?\s*(\d+\.\d+(?:\.\d+)?)", content, re.IGNORECASE)
        version = version_match.group(1) if version_match else "1.0.0"

        # Extract description (first paragraph after title)
        description = None
        for sent in doc.sents:
            if len(sent.text.split()) > 5:
                description = sent.text
                break

        return APIMetadata(
            title=title,
            version=version,
            description=description,
        )

    def _extract_endpoints(self, doc: Doc, content: str) -> List[Endpoint]:
        """Extract endpoint definitions from document."""
        endpoints = []

        # Split content into sections
        sections = self._split_into_sections(content)

        for section in sections:
            # Look for endpoint patterns
            endpoint_matches = self._find_endpoint_patterns(section)

            for method, path, description in endpoint_matches:
                try:
                    endpoint = self._build_endpoint(method, path, description, section)
                    endpoints.append(endpoint)
                except Exception as e:
                    logger.warning(f"Failed to parse endpoint {method} {path}: {e}")

        return endpoints

    def _split_into_sections(self, content: str) -> List[str]:
        """Split document into logical sections."""
        # Split by headers (markdown style or numbered)
        sections = re.split(r"\n#{1,3}\s+|\n\d+\.\s+", content)
        return [s.strip() for s in sections if s.strip()]

    def _find_endpoint_patterns(self, text: str) -> List[Tuple[str, str, str]]:
        """Find endpoint patterns in text."""
        endpoints = []

        # Pattern 1: Explicit method and path (e.g., "POST /api/users")
        pattern1 = r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\w\-/{}:]*)"
        matches1 = re.finditer(pattern1, text, re.IGNORECASE)

        for match in matches1:
            method = match.group(1).upper()
            path = match.group(2)
            # Extract description (next few sentences)
            desc_start = match.end()
            desc = text[desc_start : desc_start + 200].split("\n")[0].strip()
            endpoints.append((method, path, desc))

        # Pattern 2: Endpoint described in sentences
        # e.g., "The API should allow users to create a new account"
        sentences = text.split(".")
        for sent in sentences:
            # Look for action verbs and resource names
            if any(word in sent.lower() for word in ["create", "add", "new"]):
                path, method = self._infer_endpoint_from_sentence(sent, "POST")
                if path:
                    endpoints.append((method, path, sent.strip()))
            elif any(word in sent.lower() for word in ["get", "fetch", "retrieve", "list"]):
                path, method = self._infer_endpoint_from_sentence(sent, "GET")
                if path:
                    endpoints.append((method, path, sent.strip()))
            elif any(word in sent.lower() for word in ["update", "modify", "edit"]):
                path, method = self._infer_endpoint_from_sentence(sent, "PUT")
                if path:
                    endpoints.append((method, path, sent.strip()))
            elif any(word in sent.lower() for word in ["delete", "remove"]):
                path, method = self._infer_endpoint_from_sentence(sent, "DELETE")
                if path:
                    endpoints.append((method, path, sent.strip()))

        return endpoints

    def _infer_endpoint_from_sentence(self, sentence: str, default_method: str) -> Tuple[Optional[str], str]:
        """Infer endpoint path from natural language sentence."""
        doc = self.nlp(sentence.lower())

        # Look for resource nouns (plural or singular)
        resources = []
        for token in doc:
            if token.pos_ == "NOUN" and token.text not in ["api", "user", "system", "application"]:
                resources.append(token.text)

        if resources:
            # Use the first resource found
            resource = resources[0]
            # Pluralize if needed
            if not resource.endswith("s"):
                resource += "s"

            # Check if ID is mentioned
            if "{id}" in sentence or "by id" in sentence or "specific" in sentence:
                path = f"/api/{resource}/{{id}}"
            else:
                path = f"/api/{resource}"

            return path, default_method

        return None, default_method

    def _build_endpoint(
        self, method: str, path: str, description: str, context: str
    ) -> Endpoint:
        """Build an Endpoint object from extracted information."""
        # Extract parameters from path
        parameters = self._extract_parameters(path, context)

        # Extract request body if POST/PUT/PATCH
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            request_body = self._extract_request_body(context)

        # Extract response information
        responses = self._extract_responses(context)

        # Determine confidence based on extraction quality
        confidence = 0.6  # Base confidence for PRD
        if request_body and request_body.schema:
            confidence += 0.1
        if responses:
            confidence += 0.1
        if parameters:
            confidence += 0.1
        confidence = min(confidence, 0.9)  # Cap at 0.9 for PRD

        return Endpoint(
            path=path,
            method=HTTPMethod[method],
            summary=description[:100] if description else None,
            description=description,
            parameters=parameters,
            request_body=request_body,
            responses=responses if responses else [ResponseBody(status_code=200)],
            confidence=confidence,
        )

    def _extract_parameters(self, path: str, context: str) -> List[Parameter]:
        """Extract parameters from path and context."""
        parameters = []

        # Path parameters (from {id}, {userId}, etc.)
        path_params = re.findall(r"\{(\w+)\}", path)
        for param in path_params:
            parameters.append(
                Parameter(
                    name=param,
                    location="path",
                    type=FieldType.STRING,
                    description=f"Path parameter: {param}",
                    constraints=FieldConstraint(required=True),
                    confidence=0.8,
                )
            )

        # Query parameters (look for mentions in context)
        query_patterns = [
            r"query parameter[s]?[:\s]+(\w+)",
            r"filter by (\w+)",
            r"search by (\w+)",
        ]
        for pattern in query_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            for match in matches:
                parameters.append(
                    Parameter(
                        name=match,
                        location="query",
                        type=FieldType.STRING,
                        description=f"Query parameter: {match}",
                        constraints=FieldConstraint(required=False),
                        confidence=0.6,
                    )
                )

        return parameters

    def _extract_request_body(self, context: str) -> Optional[RequestBody]:
        """Extract request body schema from context."""
        # Look for field definitions
        fields = self._extract_fields(context)

        if not fields:
            return None

        return RequestBody(
            content_type="application/json",
            schema=fields,
            required=True,
            confidence=0.6,
        )

    def _extract_responses(self, context: str) -> List[ResponseBody]:
        """Extract response schemas from context."""
        responses = []

        # Look for success response
        fields = self._extract_fields(context, is_response=True)

        if fields:
            responses.append(
                ResponseBody(
                    status_code=200,
                    content_type="application/json",
                    schema=fields,
                    description="Successful response",
                    confidence=0.6,
                )
            )

        return responses

    def _extract_fields(self, context: str, is_response: bool = False) -> Dict[str, FieldDefinition]:
        """Extract field definitions from context with confidence scoring."""
        fields = {}

        # Pattern: "field_name: type (description)"
        # or "field_name (type): description"
        patterns = [
            r"(\w+)\s*:\s*(\w+)\s*(?:\(([^)]+)\))?",
            r"(\w+)\s*\((\w+)\)\s*:?\s*([^,\n]*)",
            r"-\s*(\w+)\s*:\s*(\w+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, context)
            for match in matches:
                field_name = match[0]
                field_type_str = match[1].lower() if len(match) > 1 else "string"
                description = match[2] if len(match) > 2 else None

                # Map type string to FieldType
                field_type = self.field_types_map.get(field_type_str, FieldType.STRING)

                # Extract constraints with confidence scoring
                constraint, constraint_confidence = self._extract_field_constraints(
                    field_name, context
                )

                # Calculate field-level confidence
                field_confidence = self._calculate_field_confidence(
                    field_name,
                    field_type_str,
                    description,
                    constraint,
                    constraint_confidence,
                    context
                )

                fields[field_name] = FieldDefinition(
                    name=field_name,
                    type=field_type,
                    description=description,
                    constraints=constraint,
                    confidence=field_confidence,
                )

        return fields

    def _extract_field_constraints(
        self, field_name: str, context: str
    ) -> Tuple[FieldConstraint, float]:
        """Extract field constraints with confidence scores."""
        constraint = FieldConstraint()
        confidence_scores = []

        # Check for "required" keyword
        required_patterns = [
            rf"{field_name}\s+(?:is|must be|should be)?\s*required",
            rf"required\s+(?:field|parameter)[s]?.*{field_name}",
            rf"{field_name}.*\(required\)",
        ]

        required_confidence = 0.0
        for pattern in required_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                constraint.required = True
                required_confidence = 0.9  # High confidence for explicit mention
                break

        if not constraint.required:
            # Check for "optional" keyword
            optional_patterns = [
                rf"{field_name}.*optional",
                rf"optional.*{field_name}",
            ]
            for pattern in optional_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    constraint.required = False
                    required_confidence = 0.8
                    break

        if required_confidence > 0:
            confidence_scores.append(required_confidence)

        # Extract numeric constraints
        min_pattern = rf"{field_name}.*(?:min|minimum|at least|greater than)\s+(\d+)"
        max_pattern = rf"{field_name}.*(?:max|maximum|at most|less than)\s+(\d+)"

        min_match = re.search(min_pattern, context, re.IGNORECASE)
        if min_match:
            constraint.minimum = int(min_match.group(1))
            confidence_scores.append(0.85)

        max_match = re.search(max_pattern, context, re.IGNORECASE)
        if max_match:
            constraint.maximum = int(max_match.group(1))
            confidence_scores.append(0.85)

        # Extract length constraints
        minlen_pattern = rf"{field_name}.*(?:min|minimum)\s+length\s+(\d+)"
        maxlen_pattern = rf"{field_name}.*(?:max|maximum)\s+length\s+(\d+)"

        minlen_match = re.search(minlen_pattern, context, re.IGNORECASE)
        if minlen_match:
            constraint.min_length = int(minlen_match.group(1))
            confidence_scores.append(0.85)

        maxlen_match = re.search(maxlen_pattern, context, re.IGNORECASE)
        if maxlen_match:
            constraint.max_length = int(maxlen_match.group(1))
            confidence_scores.append(0.85)

        # Extract format constraints
        format_patterns = {
            "email": [rf"{field_name}.*email", r"email.*{field_name}"],
            "uri": [rf"{field_name}.*(?:url|uri)", r"(?:url|uri).*{field_name}"],
            "uuid": [rf"{field_name}.*uuid", r"uuid.*{field_name}"],
            "date": [rf"{field_name}.*date", r"date.*{field_name}"],
            "date-time": [rf"{field_name}.*(?:datetime|timestamp)", r"(?:datetime|timestamp).*{field_name}"],
        }

        for format_name, patterns in format_patterns.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    constraint.format = format_name
                    confidence_scores.append(0.80)
                    break

        # Calculate average confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5

        return constraint, overall_confidence

    def _calculate_field_confidence(
        self,
        field_name: str,
        field_type: str,
        description: Optional[str],
        constraint: FieldConstraint,
        constraint_confidence: float,
        context: str
    ) -> float:
        """
        Calculate confidence score for extracted field.

        Factors:
        1. Linguistic certainty (modal verbs: must, should, may)
        2. Explicit type definition
        3. Constraint extraction quality
        4. Description presence
        5. Context specificity
        """
        confidence_factors = []

        # Factor 1: Linguistic certainty
        certainty_score = self._assess_linguistic_certainty(field_name, context)
        confidence_factors.append(certainty_score)

        # Factor 2: Explicit type definition
        if field_type in self.field_types_map:
            confidence_factors.append(0.8)  # Known type
        else:
            confidence_factors.append(0.5)  # Inferred type

        # Factor 3: Constraint quality
        if constraint_confidence > 0:
            confidence_factors.append(constraint_confidence)

        # Factor 4: Description presence
        if description and len(description) > 10:
            confidence_factors.append(0.7)
        elif description:
            confidence_factors.append(0.5)

        # Factor 5: Context specificity (how many times field mentioned)
        mention_count = context.lower().count(field_name.lower())
        if mention_count >= 3:
            confidence_factors.append(0.8)
        elif mention_count >= 2:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.6)

        # Calculate weighted average (emphasize certainty and constraint quality)
        if len(confidence_factors) >= 3:
            weights = [0.3, 0.2, 0.3, 0.1, 0.1][:len(confidence_factors)]
            weighted_confidence = sum(
                f * w for f, w in zip(confidence_factors, weights)
            ) / sum(weights)
        else:
            weighted_confidence = sum(confidence_factors) / len(confidence_factors)

        # Cap PRD confidence at 0.9 (never 100% certain from natural language)
        return min(weighted_confidence, 0.9)

    def _assess_linguistic_certainty(self, field_name: str, context: str) -> float:
        """
        Assess linguistic certainty from modal verbs and hedge words.

        High certainty (0.9): "must", "required", "will"
        Medium certainty (0.7): "should", "expected"
        Low certainty (0.5): "may", "might", "could", "optional"
        """
        # Find sentences mentioning the field
        sentences = [s for s in context.split(".") if field_name in s]

        if not sentences:
            return 0.5  # Default uncertainty

        sentence = sentences[0].lower()

        # High certainty indicators
        high_certainty_words = ["must", "required", "will", "shall", "always"]
        if any(word in sentence for word in high_certainty_words):
            return 0.9

        # Medium certainty indicators
        medium_certainty_words = ["should", "expected", "typically", "usually"]
        if any(word in sentence for word in medium_certainty_words):
            return 0.7

        # Low certainty indicators
        low_certainty_words = ["may", "might", "could", "optional", "possibly", "potentially"]
        if any(word in sentence for word in low_certainty_words):
            return 0.5

        # No modal verbs found - moderate confidence
        return 0.6

    def _calculate_confidence(self, endpoints: List[Endpoint]) -> float:
        """Calculate overall confidence score for the extracted spec."""
        if not endpoints:
            return 0.3

        total_confidence = sum(ep.confidence for ep in endpoints)
        return total_confidence / len(endpoints)


def parse_prd(prd_path: Path) -> UnifiedAPISpec:
    """
    Convenience function to parse a PRD document.

    Args:
        prd_path: Path to PRD document

    Returns:
        UnifiedAPISpec instance
    """
    parser = PRDParser()
    return parser.parse_file(prd_path)
