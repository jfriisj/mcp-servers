"""
Study Buddy GUI - Input Validation System

Provides comprehensive input validation and sanitization to prevent injection attacks,
validate file paths, and ensure data integrity throughout the application.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Chain of Responsibility Pattern
SOLID: SRP (validation rules), OCP (extensible validators), DIP (rule abstraction)
"""

import html
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set, Union

from gui.error_handling import (
    get_debug_logger,
    get_error_tracker,
    ErrorSeverity,
    ErrorCategory,
)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"  # Information/warning
    WARNING = "warning"  # Potential issue
    ERROR = "error"  # Validation failed
    CRITICAL = "critical"  # Security threat detected


class ValidationType(Enum):
    """Types of validation to perform."""

    LENGTH = auto()  # String length validation
    FORMAT = auto()  # Format/pattern validation
    CONTENT = auto()  # Content safety validation
    PATH = auto()  # File path validation
    ENCODING = auto()  # Character encoding validation
    INJECTION = auto()  # Injection attack detection


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_valid: bool
    original_input: Any
    sanitized_input: Optional[Any] = None
    severity: ValidationSeverity = ValidationSeverity.INFO
    validation_type: Optional[ValidationType] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """Allow boolean evaluation."""
        return self.is_valid


class IValidationRule(ABC):
    """Interface for validation rules."""

    @abstractmethod
    def validate(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate input value.

        Args:
            input_value: Value to validate
            context: Optional validation context

        Returns:
            ValidationResult with validation outcome
        """
        pass

    @abstractmethod
    def get_rule_name(self) -> str:
        """Get descriptive name for this rule."""
        pass


class LengthValidationRule(IValidationRule):
    """Validates string length constraints."""

    def __init__(self, min_length: int = 0, max_length: int = 10000):
        self.min_length = min_length
        self.max_length = max_length

    def validate(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate string length."""
        if not isinstance(input_value, str):
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.LENGTH,
                message=f"Expected string, got {type(input_value).__name__}",
            )

        length = len(input_value)

        if length < self.min_length:
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.LENGTH,
                message=f"Input too short: {length} < {self.min_length}",
                details={"actual_length": length, "min_length": self.min_length},
            )

        if length > self.max_length:
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                sanitized_input=input_value[: self.max_length],
                severity=ValidationSeverity.WARNING,
                validation_type=ValidationType.LENGTH,
                message=f"Input truncated: {length} > {self.max_length}",
                details={"actual_length": length, "max_length": self.max_length},
            )

        return ValidationResult(
            is_valid=True,
            original_input=input_value,
            sanitized_input=input_value,
            validation_type=ValidationType.LENGTH,
            message="Length validation passed",
        )

    def get_rule_name(self) -> str:
        """Get rule name."""
        return f"LengthValidation({self.min_length}-{self.max_length})"


class FormatValidationRule(IValidationRule):
    """Validates input format using regex patterns."""

    def __init__(self, pattern: Union[str, Pattern], format_name: str = "custom"):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.format_name = format_name

    def validate(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate input format."""
        if not isinstance(input_value, str):
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.FORMAT,
                message=f"Expected string for format validation, got {type(input_value).__name__}",
            )

        if self.pattern.match(input_value):
            return ValidationResult(
                is_valid=True,
                original_input=input_value,
                sanitized_input=input_value,
                validation_type=ValidationType.FORMAT,
                message=f"Format validation passed: {self.format_name}",
            )
        else:
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.FORMAT,
                message=f"Invalid format: expected {self.format_name}",
                details={
                    "pattern": self.pattern.pattern,
                    "format_name": self.format_name,
                },
            )

    def get_rule_name(self) -> str:
        """Get rule name."""
        return f"FormatValidation({self.format_name})"


class PathValidationRule(IValidationRule):
    """Validates file paths for safety and accessibility."""

    def __init__(
        self,
        allowed_extensions: Optional[Set[str]] = None,
        allow_relative: bool = False,
    ):
        self.allowed_extensions = allowed_extensions or {
            ".pdf",
            ".docx",
            ".pptx",
            ".md",
            ".txt",
        }
        self.allow_relative = allow_relative

        # Dangerous path patterns
        self.dangerous_patterns = [
            r"\.\.",  # Directory traversal
            r"[<>:\"|?*]",  # Invalid Windows filename chars
            r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$",  # Reserved Windows names
            r"^\s+|\s+$",  # Leading/trailing whitespace
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns
        ]

    def validate(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate file path."""
        if not isinstance(input_value, str):
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.PATH,
                message=f"Expected string path, got {type(input_value).__name__}",
            )

        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(input_value):
                return ValidationResult(
                    is_valid=False,
                    original_input=input_value,
                    severity=ValidationSeverity.CRITICAL,
                    validation_type=ValidationType.PATH,
                    message=f"Dangerous path pattern detected: {pattern.pattern}",
                    details={"matched_pattern": pattern.pattern},
                )

        path = Path(input_value)

        # Check if relative paths are allowed
        if not self.allow_relative and not path.is_absolute():
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.PATH,
                message="Relative paths not allowed",
                details={"is_absolute": path.is_absolute()},
            )

        # Check file extension
        if (
            self.allowed_extensions
            and path.suffix.lower() not in self.allowed_extensions
        ):
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.WARNING,
                validation_type=ValidationType.PATH,
                message=f"File extension not allowed: {path.suffix}",
                details={
                    "extension": path.suffix,
                    "allowed_extensions": list(self.allowed_extensions),
                },
            )

        # Normalize path
        try:
            normalized_path = str(path.resolve())
        except (OSError, ValueError) as e:
            return ValidationResult(
                is_valid=False,
                original_input=input_value,
                severity=ValidationSeverity.ERROR,
                validation_type=ValidationType.PATH,
                message=f"Path resolution failed: {e}",
                details={"error": str(e)},
            )

        return ValidationResult(
            is_valid=True,
            original_input=input_value,
            sanitized_input=normalized_path,
            validation_type=ValidationType.PATH,
            message="Path validation passed",
            details={"normalized_path": normalized_path},
        )

    def get_rule_name(self) -> str:
        """Get rule name."""
        return f"PathValidation(extensions={len(self.allowed_extensions)}, relative={self.allow_relative})"


class InjectionValidationRule(IValidationRule):
    """Detects potential injection attacks in input."""

    def __init__(self):
        # Common injection attack patterns
        self.injection_patterns = [
            # SQL injection
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|;|'|\"|`)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            # Command injection
            r"[;&|`$]",
            r"\b(rm|del|format|shutdown|reboot|halt)\b",
            # Script injection
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            # Path traversal
            r"\.\.[/\\]",
            r"%2e%2e[/\\]",
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.injection_patterns
        ]

    def validate(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Detect injection attacks."""
        if not isinstance(input_value, str):
            # Non-string inputs are generally safe from injection
            return ValidationResult(
                is_valid=True,
                original_input=input_value,
                sanitized_input=input_value,
                validation_type=ValidationType.INJECTION,
                message="Non-string input is safe from injection",
            )

        # Check each pattern
        for i, pattern in enumerate(self.compiled_patterns):
            match = pattern.search(input_value)
            if match:
                return ValidationResult(
                    is_valid=False,
                    original_input=input_value,
                    severity=ValidationSeverity.CRITICAL,
                    validation_type=ValidationType.INJECTION,
                    message=f"Potential injection attack detected: {self.injection_patterns[i]}",
                    details={
                        "matched_pattern": self.injection_patterns[i],
                        "match_text": match.group(),
                        "match_position": match.span(),
                    },
                )

        # Additional safety: HTML escape the input
        escaped_input = html.escape(input_value)

        return ValidationResult(
            is_valid=True,
            original_input=input_value,
            sanitized_input=escaped_input,
            validation_type=ValidationType.INJECTION,
            message="Injection validation passed",
            details={"html_escaped": escaped_input != input_value},
        )

    def get_rule_name(self) -> str:
        """Get rule name."""
        return "InjectionValidation"


class EncodingValidationRule(IValidationRule):
    """Validates character encoding and handles encoding issues."""

    def __init__(self, encoding: str = "utf-8", strict: bool = False):
        self.encoding = encoding
        self.strict = strict

    def validate(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate character encoding."""
        if isinstance(input_value, str):
            # String is already decoded, check if it can be encoded
            try:
                encoded = input_value.encode(self.encoding)
                decoded = encoded.decode(self.encoding)

                if decoded == input_value:
                    return ValidationResult(
                        is_valid=True,
                        original_input=input_value,
                        sanitized_input=input_value,
                        validation_type=ValidationType.ENCODING,
                        message=f"Encoding validation passed: {self.encoding}",
                    )
                else:
                    return ValidationResult(
                        is_valid=not self.strict,
                        original_input=input_value,
                        sanitized_input=decoded if not self.strict else None,
                        severity=ValidationSeverity.WARNING
                        if not self.strict
                        else ValidationSeverity.ERROR,
                        validation_type=ValidationType.ENCODING,
                        message="Encoding round-trip changed string",
                        details={
                            "original_length": len(input_value),
                            "decoded_length": len(decoded),
                        },
                    )

            except UnicodeEncodeError as e:
                if self.strict:
                    return ValidationResult(
                        is_valid=False,
                        original_input=input_value,
                        severity=ValidationSeverity.ERROR,
                        validation_type=ValidationType.ENCODING,
                        message=f"Encoding failed: {e}",
                        details={"encoding": self.encoding, "error": str(e)},
                    )
                else:
                    # Replace problematic characters
                    sanitized = input_value.encode(
                        self.encoding, errors="replace"
                    ).decode(self.encoding)
                    return ValidationResult(
                        is_valid=True,
                        original_input=input_value,
                        sanitized_input=sanitized,
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.ENCODING,
                        message="Encoding issues fixed by replacement",
                        details={
                            "encoding": self.encoding,
                            "characters_replaced": input_value != sanitized,
                        },
                    )

        elif isinstance(input_value, bytes):
            # Bytes need to be decoded
            try:
                decoded = input_value.decode(self.encoding)
                return ValidationResult(
                    is_valid=True,
                    original_input=input_value,
                    sanitized_input=decoded,
                    validation_type=ValidationType.ENCODING,
                    message=f"Bytes decoded successfully: {self.encoding}",
                )

            except UnicodeDecodeError as e:
                if self.strict:
                    return ValidationResult(
                        is_valid=False,
                        original_input=input_value,
                        severity=ValidationSeverity.ERROR,
                        validation_type=ValidationType.ENCODING,
                        message=f"Decoding failed: {e}",
                        details={"encoding": self.encoding, "error": str(e)},
                    )
                else:
                    # Replace problematic bytes
                    sanitized = input_value.decode(self.encoding, errors="replace")
                    return ValidationResult(
                        is_valid=True,
                        original_input=input_value,
                        sanitized_input=sanitized,
                        severity=ValidationSeverity.WARNING,
                        validation_type=ValidationType.ENCODING,
                        message="Decoding issues fixed by replacement",
                        details={"encoding": self.encoding},
                    )

        else:
            # Non-string, non-bytes input
            return ValidationResult(
                is_valid=True,
                original_input=input_value,
                sanitized_input=input_value,
                validation_type=ValidationType.ENCODING,
                message="Non-text input skipped encoding validation",
            )

    def get_rule_name(self) -> str:
        """Get rule name."""
        return f"EncodingValidation({self.encoding}, strict={self.strict})"


class InputValidator:
    """
    Central input validation system.

    Responsibilities:
    - Coordinate multiple validation rules
    - Provide pre-configured validators for common scenarios
    - Track validation statistics and security events
    - Integrate with error handling and logging systems
    """

    def __init__(self):
        self._rules: List[IValidationRule] = []
        self._validation_stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "critical_security_events": 0,
        }

        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()
        self._lock = threading.RLock()

        # Setup default rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup commonly used validation rules."""
        # Always check for injection attacks
        self.add_rule(InjectionValidationRule())

        # Default encoding validation
        self.add_rule(EncodingValidationRule())

        # Basic length limits
        self.add_rule(LengthValidationRule(min_length=0, max_length=100000))

    def add_rule(self, rule: IValidationRule) -> None:
        """Add validation rule."""
        with self._lock:
            if rule not in self._rules:
                self._rules.append(rule)
                self._logger.debug(f"Added validation rule: {rule.get_rule_name()}")

    def remove_rule(self, rule: IValidationRule) -> None:
        """Remove validation rule."""
        with self._lock:
            if rule in self._rules:
                self._rules.remove(rule)
                self._logger.debug(f"Removed validation rule: {rule.get_rule_name()}")

    def validate_input(
        self,
        input_value: Any,
        context: Optional[Dict[str, Any]] = None,
        stop_on_first_failure: bool = True,
    ) -> List[ValidationResult]:
        """
        Validate input using all configured rules.

        Args:
            input_value: Value to validate
            context: Optional validation context
            stop_on_first_failure: Stop on first validation failure

        Returns:
            List of ValidationResult objects
        """
        results = []

        with self._lock:
            self._validation_stats["total_validations"] += 1

            for rule in self._rules:
                try:
                    result = rule.validate(input_value, context)
                    results.append(result)

                    # Track critical security events
                    if result.severity == ValidationSeverity.CRITICAL:
                        self._validation_stats["critical_security_events"] += 1

                        # Report to error tracker
                        self._error_tracker.capture_error(
                            exception=SecurityError(result.message),
                            severity=ErrorSeverity.CRITICAL,
                            category=ErrorCategory.SECURITY,
                            user_action="Input validation",
                            operation_context={
                                "rule_name": rule.get_rule_name(),
                                "validation_type": result.validation_type.name
                                if result.validation_type
                                else None,
                                "input_type": type(input_value).__name__,
                                "input_preview": str(input_value)[:100],
                                "context": context,
                            },
                        )

                    # Stop on failure if requested
                    if stop_on_first_failure and not result.is_valid:
                        break

                except Exception as e:
                    # Rule validation failed
                    error_result = ValidationResult(
                        is_valid=False,
                        original_input=input_value,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation rule failed: {rule.get_rule_name()} - {e}",
                        details={"rule_name": rule.get_rule_name(), "error": str(e)},
                    )
                    results.append(error_result)

                    self._logger.error(
                        f"Validation rule failed: {rule.get_rule_name()} - {e}"
                    )

                    if stop_on_first_failure:
                        break

            # Update statistics
            if all(result.is_valid for result in results):
                self._validation_stats["passed_validations"] += 1
            else:
                self._validation_stats["failed_validations"] += 1

        return results

    def validate_and_sanitize(
        self, input_value: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate input and return sanitized result.

        Args:
            input_value: Value to validate and sanitize
            context: Optional validation context

        Returns:
            Combined ValidationResult with sanitized input
        """
        results = self.validate_input(input_value, context, stop_on_first_failure=False)

        # Find the most severe issue
        most_severe = ValidationSeverity.INFO
        combined_messages = []
        final_sanitized_input = input_value

        for result in results:
            if result.severity.value > most_severe.value:
                most_severe = result.severity

            combined_messages.append(result.message)

            # Use sanitized input from successful validations
            if result.is_valid and result.sanitized_input is not None:
                final_sanitized_input = result.sanitized_input

        # Determine overall validity
        is_valid = all(result.is_valid for result in results)

        return ValidationResult(
            is_valid=is_valid,
            original_input=input_value,
            sanitized_input=final_sanitized_input if is_valid else None,
            severity=most_severe,
            message="; ".join(combined_messages),
            details={
                "rule_count": len(results),
                "individual_results": [
                    {
                        "rule": results[i].validation_type.name
                        if results[i].validation_type is not None
                        else "unknown",
                        "valid": results[i].is_valid,
                        "message": results[i].message,
                    }
                    for i in range(len(results))
                ],
            },
        )

    def create_file_path_validator(
        self, allowed_extensions: Optional[Set[str]] = None
    ) -> "InputValidator":
        """Create validator specialized for file paths."""
        validator = InputValidator()
        validator._rules = []  # Clear default rules

        # Add path-specific rules
        validator.add_rule(PathValidationRule(allowed_extensions=allowed_extensions))
        validator.add_rule(InjectionValidationRule())
        validator.add_rule(EncodingValidationRule())

        return validator

    def create_text_content_validator(
        self, max_length: int = 1000000
    ) -> "InputValidator":
        """Create validator for text content."""
        validator = InputValidator()
        validator._rules = []  # Clear default rules

        # Add content-specific rules
        validator.add_rule(LengthValidationRule(max_length=max_length))
        validator.add_rule(InjectionValidationRule())
        validator.add_rule(EncodingValidationRule(strict=False))

        return validator

    def create_filename_validator(self) -> "InputValidator":
        """Create validator for filenames."""
        validator = InputValidator()
        validator._rules = []  # Clear default rules

        # Add filename-specific rules
        validator.add_rule(LengthValidationRule(min_length=1, max_length=255))
        validator.add_rule(
            FormatValidationRule(
                pattern=r"^[a-zA-Z0-9._\-\s]+$", format_name="safe_filename"
            )
        )
        validator.add_rule(InjectionValidationRule())
        validator.add_rule(EncodingValidationRule())

        return validator

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        with self._lock:
            return self._validation_stats.copy()

    def reset_statistics(self) -> None:
        """Reset validation statistics."""
        with self._lock:
            self._validation_stats = {
                "total_validations": 0,
                "passed_validations": 0,
                "failed_validations": 0,
                "critical_security_events": 0,
            }
            self._logger.info("Validation statistics reset")


class SecurityError(Exception):
    """Exception raised for security-related validation failures."""

    pass


# Global validator instance
_input_validator: Optional[InputValidator] = None
_input_validator_lock = threading.Lock()


def get_input_validator() -> InputValidator:
    """
    Get global input validator instance (singleton pattern).

    Returns:
        InputValidator instance
    """
    global _input_validator

    if _input_validator is None:
        with _input_validator_lock:
            if _input_validator is None:
                _input_validator = InputValidator()

    return _input_validator


# Convenience functions
def validate_file_path(
    file_path: str, allowed_extensions: Optional[Set[str]] = None
) -> ValidationResult:
    """Validate file path with security checks."""
    validator = get_input_validator()
    path_validator = validator.create_file_path_validator(allowed_extensions)
    return path_validator.validate_and_sanitize(file_path)


def validate_text_content(content: str, max_length: int = 1000000) -> ValidationResult:
    """Validate text content for safety."""
    validator = get_input_validator()
    content_validator = validator.create_text_content_validator(max_length)
    return content_validator.validate_and_sanitize(content)


def validate_filename(filename: str) -> ValidationResult:
    """Validate filename for safety."""
    validator = get_input_validator()
    filename_validator = validator.create_filename_validator()
    return filename_validator.validate_and_sanitize(filename)


def sanitize_input(input_value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
    """Quick sanitization of input value."""
    validator = get_input_validator()
    result = validator.validate_and_sanitize(input_value, context)
    return result.sanitized_input if result.is_valid else input_value
