"""
Input Validation and Security
Comprehensive input validation, sanitization, and security measures
"""

import html
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, Union

import bleach
import validators

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""

    pass


class InputType(Enum):
    """Input validation types"""

    EMAIL = "email"
    USERNAME = "username"
    PASSWORD = "password"
    TEXT = "text"
    HTML = "html"
    URL = "url"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    UUID = "uuid"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"


class SecurityValidator:
    """Input validation and security class"""

    def __init__(self):
        # HTML sanitization configuration
        self.allowed_html_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "ol",
            "ul",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
            "a",
            "code",
            "pre",
        ]

        self.allowed_html_attributes = {
            "a": ["href", "title"],
            "code": ["class"],
            "pre": ["class"],
        }

        # Regex patterns
        self.patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "username": re.compile(r"^[a-zA-Z0-9_]{3,30}$"),
            "password": re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"),
            "phone": re.compile(
                r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"
            ),
            "uuid": re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            ),
            "credit_card": re.compile(r"^[0-9]{13,19}$"),
            "sql_injection": re.compile(
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                re.IGNORECASE,
            ),
            "xss": re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
            "path_traversal": re.compile(r"\.\.[\\/]"),
        }

        # Common malicious patterns
        self.malicious_patterns = [
            # SQL injection patterns
            r"'.*?(\b(OR|AND)\b).*?'",
            r'"\s*(OR|AND)\s*"',
            r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP)\b",
            # XSS patterns
            r"<script.*?>",
            r"javascript:",
            r"on\w+\s*=",
            r"expression\s*\(",
            # Command injection
            r";.*?\b(rm|wget|curl|nc|bash|sh|python|perl|php)\b",
            r"\|.*?\b(cat|ls|ps|id|whoami)\b",
            # Path traversal
            r"\.\.[\\/]",
            r"[\\/]etc[\\/]passwd",
            r"[\\/]windows[\\/]system32",
        ]

    def validate_input(
        self,
        value: Any,
        input_type: InputType,
        required: bool = True,
        min_length: int = None,
        max_length: int = None,
        custom_pattern: str = None,
    ) -> Any:
        """Validate input based on type"""

        try:
            # Check if required
            if required and (value is None or value == ""):
                raise ValidationError(f"{input_type.value} is required")

            if value is None or value == "":
                return value

            # Convert to string for most validations
            str_value = str(value).strip()

            # Check length
            if min_length and len(str_value) < min_length:
                raise ValidationError(
                    f"{input_type.value} must be at least {min_length} characters"
                )

            if max_length and len(str_value) > max_length:
                raise ValidationError(
                    f"{input_type.value} must not exceed {max_length} characters"
                )

            # Check for malicious patterns
            self._check_malicious_patterns(str_value)

            # Validate based on type
            if input_type == InputType.EMAIL:
                return self._validate_email(str_value)
            elif input_type == InputType.USERNAME:
                return self._validate_username(str_value)
            elif input_type == InputType.PASSWORD:
                return self._validate_password(str_value)
            elif input_type == InputType.TEXT:
                return self._validate_text(str_value)
            elif input_type == InputType.HTML:
                return self._validate_html(str_value)
            elif input_type == InputType.URL:
                return self._validate_url(str_value)
            elif input_type == InputType.INTEGER:
                return self._validate_integer(value)
            elif input_type == InputType.DECIMAL:
                return self._validate_decimal(value)
            elif input_type == InputType.DATE:
                return self._validate_date(str_value)
            elif input_type == InputType.UUID:
                return self._validate_uuid(str_value)
            elif input_type == InputType.PHONE:
                return self._validate_phone(str_value)
            elif input_type == InputType.CREDIT_CARD:
                return self._validate_credit_card(str_value)

            # Custom pattern validation
            if custom_pattern and not re.match(custom_pattern, str_value):
                raise ValidationError(f"{input_type.value} format is invalid")

            return str_value

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {e}")
            raise ValidationError(f"Invalid {input_type.value}")

    def _check_malicious_patterns(self, value: str):
        """Check for common malicious patterns"""

        for pattern in self.malicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Malicious pattern detected: {pattern[:20]}...")
                raise ValidationError("Input contains potentially malicious content")

    def _validate_email(self, email: str) -> str:
        """Validate email address"""

        if not self.patterns["email"].match(email):
            raise ValidationError("Invalid email format")

        # Additional checks
        if ".." in email or email.startswith(".") or email.endswith("."):
            raise ValidationError("Invalid email format")

        return email.lower()

    def _validate_username(self, username: str) -> str:
        """Validate username"""

        if not self.patterns["username"].match(username):
            raise ValidationError(
                "Username must be 3-30 characters, alphanumeric and underscore only"
            )

        # Check against reserved words
        reserved_words = ["admin", "root", "user", "test", "api", "www", "mail"]
        if username.lower() in reserved_words:
            raise ValidationError("Username is reserved")

        return username.lower()

    def _validate_password(self, password: str) -> str:
        """Validate password strength"""

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password must contain at least one special character"
            )

        # Check against common passwords
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
        if password.lower() in common_passwords:
            raise ValidationError("Password is too common")

        return password

    def _validate_text(self, text: str) -> str:
        """Validate and sanitize text"""

        # Remove HTML tags
        text = bleach.clean(text, tags=[], strip=True)

        # Escape HTML entities
        text = html.escape(text)

        return text

    def _validate_html(self, html_text: str) -> str:
        """Validate and sanitize HTML"""

        # Sanitize HTML
        clean_html = bleach.clean(
            html_text,
            tags=self.allowed_html_tags,
            attributes=self.allowed_html_attributes,
            strip=True,
        )

        return clean_html

    def _validate_url(self, url: str) -> str:
        """Validate URL"""

        if not validators.url(url):
            raise ValidationError("Invalid URL format")

        # Additional security checks
        if not url.startswith(("http://", "https://")):
            raise ValidationError("URL must use HTTP or HTTPS protocol")

        # Block dangerous protocols
        dangerous_protocols = ["javascript:", "data:", "vbscript:", "file:"]
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                raise ValidationError("Dangerous URL protocol detected")

        return url

    def _validate_integer(self, value: Union[str, int]) -> int:
        """Validate integer"""

        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid integer value")

    def _validate_decimal(self, value: Union[str, float, Decimal]) -> Decimal:
        """Validate decimal/monetary value"""

        try:
            decimal_value = Decimal(str(value))

            # Check for reasonable range
            if decimal_value < 0:
                raise ValidationError("Decimal value cannot be negative")

            if decimal_value > Decimal("999999999.99"):
                raise ValidationError("Decimal value too large")

            return decimal_value
        except (InvalidOperation, ValueError):
            raise ValidationError("Invalid decimal value")

    def _validate_date(self, date_str: str) -> datetime:
        """Validate date string"""

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            raise ValidationError("Invalid date format")
        except Exception:
            raise ValidationError("Invalid date")

    def _validate_uuid(self, uuid_str: str) -> str:
        """Validate UUID"""

        if not self.patterns["uuid"].match(uuid_str.lower()):
            raise ValidationError("Invalid UUID format")

        return uuid_str.lower()

    def _validate_phone(self, phone: str) -> str:
        """Validate phone number"""

        # Remove common formatting
        clean_phone = re.sub(r"[-.\s()]", "", phone)

        if not clean_phone.isdigit():
            raise ValidationError("Phone number must contain only digits")

        if len(clean_phone) < 10 or len(clean_phone) > 15:
            raise ValidationError("Phone number must be 10-15 digits")

        return clean_phone

    def _validate_credit_card(self, card_number: str) -> str:
        """Validate credit card number"""

        # Remove spaces and dashes
        clean_number = re.sub(r"[\s-]", "", card_number)

        if not self.patterns["credit_card"].match(clean_number):
            raise ValidationError("Invalid credit card format")

        # Luhn algorithm check
        if not self._luhn_check(clean_number):
            raise ValidationError("Invalid credit card number")

        return clean_number

    def _luhn_check(self, card_number: str) -> bool:
        """Luhn algorithm for credit card validation"""

        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)

        for d in even_digits:
            checksum += sum(digits_of(d * 2))

        return checksum % 10 == 0

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""

        # Remove path traversal attempts
        filename = filename.replace("..", "")

        # Keep only alphanumeric, dots, dashes, and underscores
        filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1)
            filename = name[:250] + "." + ext

        return filename

    def validate_json_schema(
        self, data: Dict[str, Any], schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data against JSON schema"""

        validated_data = {}

        for field, rules in schema.items():
            value = data.get(field)

            # Check if required
            if rules.get("required", False) and value is None:
                raise ValidationError(f"Field '{field}' is required")

            if value is not None:
                # Validate type
                input_type = InputType(rules.get("type", "text"))
                validated_value = self.validate_input(
                    value=value,
                    input_type=input_type,
                    required=rules.get("required", False),
                    min_length=rules.get("min_length"),
                    max_length=rules.get("max_length"),
                    custom_pattern=rules.get("pattern"),
                )
                validated_data[field] = validated_value

        return validated_data


# Global validator instance
security_validator = SecurityValidator()


# Helper functions
def validate_email(email: str) -> str:
    """Validate email address"""
    return security_validator.validate_input(email, InputType.EMAIL)


def validate_username(username: str) -> str:
    """Validate username"""
    return security_validator.validate_input(username, InputType.USERNAME)


def validate_password(password: str) -> str:
    """Validate password"""
    return security_validator.validate_input(password, InputType.PASSWORD)


def sanitize_text(text: str) -> str:
    """Sanitize text input"""
    return security_validator.validate_input(text, InputType.TEXT)


def sanitize_html(html_text: str) -> str:
    """Sanitize HTML input"""
    return security_validator.validate_input(html_text, InputType.HTML)


def validate_url(url: str) -> str:
    """Validate URL"""
    return security_validator.validate_input(url, InputType.URL)


def validate_decimal_amount(amount: Union[str, float, Decimal]) -> Decimal:
    """Validate monetary amount"""
    return security_validator.validate_input(amount, InputType.DECIMAL)


# Example validation schemas
USER_REGISTRATION_SCHEMA = {
    "email": {"type": "email", "required": True, "max_length": 255},
    "username": {
        "type": "username",
        "required": True,
        "min_length": 3,
        "max_length": 30,
    },
    "password": {"type": "password", "required": True, "min_length": 8},
    "full_name": {"type": "text", "required": True, "max_length": 255},
}

PAYMENT_REQUEST_SCHEMA = {
    "user_id": {"type": "text", "required": True, "max_length": 255},
    "amount": {"type": "decimal", "required": True},
    "currency": {"type": "text", "required": False, "max_length": 3},
    "description": {"type": "text", "required": False, "max_length": 500},
}

# Example usage and testing
if __name__ == "__main__":
    print(" Testing Input Validation...")

    # Test email validation
    try:
        email = validate_email("test@example.com")
        print(f"[OK] Valid email: {email}")
    except ValidationError as e:
        print(f"[ERROR] Email validation failed: {e}")

    # Test malicious input detection
    try:
        malicious_input = "'; DROP TABLE users; --"
        sanitized = sanitize_text(malicious_input)
        print(f"[ERROR] Should have caught SQL injection: {sanitized}")
    except ValidationError as e:
        print(f"[OK] Caught malicious input: {e}")

    # Test schema validation
    try:
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "full_name": "Test User",
        }

        validated = security_validator.validate_json_schema(
            user_data, USER_REGISTRATION_SCHEMA
        )
        print(f"[OK] Schema validation passed: {validated}")
    except ValidationError as e:
        print(f"[ERROR] Schema validation failed: {e}")

    print("[OK] Input Validation tests completed")
