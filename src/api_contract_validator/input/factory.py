"""
Parser Factory - Extensible framework for parsing multiple input sources

This module provides a factory pattern for creating parsers that convert
heterogeneous API contract sources into a unified representation.

Novel Contribution: Multi-modal contract fusion system supporting 5+ source types
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Type, Optional, Union
import logging

from api_contract_validator.input.normalizer.models import UnifiedAPISpec, SourceType

logger = logging.getLogger(__name__)


class BaseInputParser(ABC):
    """
    Abstract base class for all input parsers.

    Each parser converts a specific source format (OpenAPI, PRD, traffic logs,
    unit tests, database schemas) into a UnifiedAPISpec with confidence scoring.
    """

    @abstractmethod
    def parse_file(self, file_path: Union[str, Path]) -> UnifiedAPISpec:
        """
        Parse input file and convert to unified spec.

        Args:
            file_path: Path to input file or directory

        Returns:
            UnifiedAPISpec with confidence scores and provenance metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If file format is invalid
        """
        pass

    @abstractmethod
    def get_source_type(self) -> SourceType:
        """Return the source type this parser handles."""
        pass

    @abstractmethod
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to check

        Returns:
            True if parser can handle this file, False otherwise
        """
        pass

    def parse_with_fallback(
        self,
        file_path: Union[str, Path],
        default: Optional[UnifiedAPISpec] = None
    ) -> Optional[UnifiedAPISpec]:
        """
        Parse file with graceful error handling.

        Args:
            file_path: Path to parse
            default: Default value to return on error

        Returns:
            UnifiedAPISpec on success, default value on error
        """
        try:
            return self.parse_file(file_path)
        except Exception as e:
            logger.warning(
                f"Failed to parse {file_path} with {self.__class__.__name__}: {e}"
            )
            return default


class ParserRegistry:
    """
    Registry for managing parser instances.

    Maintains mappings between source types and parser classes,
    supporting both explicit type selection and auto-detection.
    """

    def __init__(self):
        self._registry: Dict[SourceType, Type[BaseInputParser]] = {}
        self._parsers: Dict[SourceType, BaseInputParser] = {}

    def register(self, source_type: SourceType, parser_class: Type[BaseInputParser]):
        """
        Register a parser class for a source type.

        Args:
            source_type: Source type enum value
            parser_class: Parser class (not instance)
        """
        self._registry[source_type] = parser_class
        logger.info(f"Registered parser {parser_class.__name__} for {source_type.value}")

    def get_parser(self, source_type: SourceType) -> BaseInputParser:
        """
        Get parser instance for a source type (lazy initialization).

        Args:
            source_type: Source type enum value

        Returns:
            Parser instance

        Raises:
            ValueError: If no parser registered for this type
        """
        if source_type not in self._parsers:
            if source_type not in self._registry:
                raise ValueError(
                    f"No parser registered for source type: {source_type.value}. "
                    f"Available types: {[t.value for t in self._registry.keys()]}"
                )

            parser_class = self._registry[source_type]
            self._parsers[source_type] = parser_class()

        return self._parsers[source_type]

    def auto_detect_parser(self, file_path: Union[str, Path]) -> Optional[BaseInputParser]:
        """
        Auto-detect appropriate parser for a file.

        Tries each registered parser's can_parse() method until one returns True.

        Args:
            file_path: Path to file

        Returns:
            Parser instance if detected, None otherwise
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        # Try each parser in priority order
        priority_order = [
            SourceType.OPENAPI,
            SourceType.DATABASE_SCHEMA,
            SourceType.API_TRAFFIC_LOGS,
            SourceType.UNIT_TESTS,
            SourceType.PRD,
        ]

        for source_type in priority_order:
            if source_type in self._registry:
                parser = self.get_parser(source_type)
                if parser.can_parse(file_path):
                    logger.info(
                        f"Auto-detected {source_type.value} parser for {file_path.name}"
                    )
                    return parser

        logger.warning(f"No parser could handle file: {file_path}")
        return None

    def list_supported_types(self) -> list[SourceType]:
        """Return list of all registered source types."""
        return list(self._registry.keys())


# Global registry instance
_global_registry = ParserRegistry()


def register_parser(source_type: SourceType, parser_class: Type[BaseInputParser]):
    """
    Register a parser class globally.

    Args:
        source_type: Source type enum value
        parser_class: Parser class to register
    """
    _global_registry.register(source_type, parser_class)


def create_parser(source_type: SourceType) -> BaseInputParser:
    """
    Factory function to create parser for a source type.

    Args:
        source_type: Source type enum value

    Returns:
        Parser instance

    Raises:
        ValueError: If no parser registered for this type

    Example:
        >>> from api_contract_validator.input.normalizer.models import SourceType
        >>> parser = create_parser(SourceType.OPENAPI)
        >>> spec = parser.parse_file("openapi.yaml")
    """
    return _global_registry.get_parser(source_type)


def auto_detect_and_parse(file_path: Union[str, Path]) -> Optional[UnifiedAPISpec]:
    """
    Auto-detect file type and parse with appropriate parser.

    Args:
        file_path: Path to input file

    Returns:
        UnifiedAPISpec if parsing succeeds, None otherwise

    Example:
        >>> spec = auto_detect_and_parse("api.yaml")
        >>> if spec:
        ...     print(f"Parsed {len(spec.endpoints)} endpoints")
    """
    parser = _global_registry.auto_detect_parser(file_path)
    if parser:
        return parser.parse_with_fallback(file_path)
    return None


def get_registry() -> ParserRegistry:
    """Get global parser registry instance."""
    return _global_registry


def parse_with_type_hint(
    file_path: Union[str, Path],
    type_hint: Optional[str] = None
) -> Optional[UnifiedAPISpec]:
    """
    Parse file with optional type hint.

    Supports format: "type:path" (e.g., "openapi:api.yaml" or "prd:requirements.md")

    Args:
        file_path: Path to input file, optionally prefixed with "type:"
        type_hint: Explicit type hint (overrides prefix)

    Returns:
        UnifiedAPISpec if parsing succeeds, None otherwise

    Example:
        >>> spec = parse_with_type_hint("openapi:api.yaml")
        >>> spec = parse_with_type_hint("api.yaml", type_hint="openapi")
    """
    file_path_str = str(file_path)

    # Extract type from "type:path" format
    if ":" in file_path_str and not type_hint:
        parts = file_path_str.split(":", 1)
        if len(parts) == 2:
            type_hint, file_path_str = parts

    # Try explicit type hint first
    if type_hint:
        try:
            source_type = SourceType(type_hint.lower())
            parser = create_parser(source_type)
            return parser.parse_with_fallback(file_path_str)
        except (ValueError, KeyError):
            logger.warning(f"Invalid type hint: {type_hint}, falling back to auto-detection")

    # Fall back to auto-detection
    return auto_detect_and_parse(file_path_str)


__all__ = [
    "BaseInputParser",
    "ParserRegistry",
    "register_parser",
    "create_parser",
    "auto_detect_and_parse",
    "parse_with_type_hint",
    "get_registry",
]
