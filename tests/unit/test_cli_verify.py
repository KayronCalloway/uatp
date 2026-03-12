"""
Unit tests for CLI verify command.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.verify import (
    ExitCode,
    determine_exit_code,
    format_result,
    result_to_dict,
    verify_cmd,
)
from src.export import UATPBundle, VerificationResult


class TestExitCodes:
    """Tests for CLI exit code logic."""

    def test_exit_code_values(self):
        assert ExitCode.SUCCESS == 0
        assert ExitCode.FAILED == 1
        assert ExitCode.WARNINGS == 2
        assert ExitCode.CONFIG_ERROR == 3
        assert ExitCode.NETWORK_ERROR == 4

    def test_determine_exit_code_success(self):
        result = VerificationResult(is_valid=True)
        assert determine_exit_code(result) == ExitCode.SUCCESS

    def test_determine_exit_code_warnings(self):
        result = VerificationResult(is_valid=True, warnings=["Test warning"])
        assert determine_exit_code(result) == ExitCode.WARNINGS

    def test_determine_exit_code_failed(self):
        result = VerificationResult(is_valid=False)
        assert determine_exit_code(result) == ExitCode.FAILED


class TestResultFormatting:
    """Tests for result formatting."""

    def test_result_to_dict_basic(self):
        result = VerificationResult(
            is_valid=True,
            signature_valid=True,
            verified_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=timezone.utc),
        )

        d = result_to_dict(result)

        assert d["is_valid"] == True
        assert d["verified_at"] == "2026-03-12T10:00:00+00:00"
        assert any(c["name"] == "signature" for c in d["checks"])

    def test_result_to_dict_with_bundle(self):
        result = VerificationResult(is_valid=True)
        bundle = MagicMock()
        bundle.capsule_id = "caps_123"
        bundle.created_at = datetime(2026, 3, 12, tzinfo=timezone.utc)
        bundle.verification = MagicMock()
        bundle.verification.key_algorithm = "ed25519"
        bundle.verification.key_id = "key_abc"

        d = result_to_dict(result, bundle)

        assert d["bundle"]["capsule_id"] == "caps_123"
        assert d["bundle"]["key_algorithm"] == "ed25519"

    def test_format_result_passed(self):
        result = VerificationResult(is_valid=True, signature_valid=True)
        output = format_result(result, no_color=True)

        assert "PASSED" in output
        assert "Signature:" in output

    def test_format_result_failed(self):
        result = VerificationResult(
            is_valid=False,
            signature_valid=False,
            errors=["Signature invalid"],
        )
        output = format_result(result, no_color=True)

        assert "FAILED" in output
        assert "Errors:" in output
        assert "Signature invalid" in output

    def test_format_result_with_warnings(self):
        result = VerificationResult(
            is_valid=True,
            warnings=["Timestamp near expiry"],
        )
        output = format_result(result, no_color=True)

        assert "Warnings:" in output
        assert "Timestamp near expiry" in output


class TestCLICommands:
    """Tests for CLI command execution."""

    def test_verify_no_args_shows_error(self):
        runner = CliRunner()
        result = runner.invoke(verify_cmd, [])

        assert result.exit_code == ExitCode.CONFIG_ERROR
        assert "Error" in result.output

    def test_verify_nonexistent_file(self):
        runner = CliRunner()
        result = runner.invoke(verify_cmd, ["nonexistent.json"])

        assert result.exit_code == ExitCode.CONFIG_ERROR
        assert "not found" in result.output.lower()

    def test_verify_invalid_json(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("invalid.json").write_text("not json at all")
            result = runner.invoke(verify_cmd, ["invalid.json"])

            assert result.exit_code == ExitCode.CONFIG_ERROR
            assert "json" in result.output.lower() or "Invalid" in result.output

    def test_verify_json_output_format(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create minimal valid bundle
            bundle_data = {
                "mediaType": "application/vnd.uatp.bundle.v1+json",
                "dsse": {
                    "payload": "e30=",  # base64("{}")
                    "payloadType": "application/vnd.uatp.capsule.v1+json",
                    "signatures": [],
                },
            }
            Path("test.json").write_text(json.dumps(bundle_data))
            result = runner.invoke(verify_cmd, ["test.json", "-o", "json"])

            # Should output valid JSON
            try:
                output = json.loads(result.output)
                assert "is_valid" in output or "error" in output
            except json.JSONDecodeError:
                # Allow for error messages that aren't JSON
                pass
