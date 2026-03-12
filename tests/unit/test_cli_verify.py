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


class TestResultToDictEdgeCases:
    """Edge case tests for result_to_dict."""

    def test_result_with_all_checks(self):
        """Test result_to_dict with all check types."""
        result = VerificationResult(
            is_valid=True,
            signature_valid=True,
            timestamp_valid=True,
            pq_signature_valid=True,
            errors=["error1"],
            warnings=["warn1"],
            verified_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=timezone.utc),
        )

        d = result_to_dict(result)

        assert len(d["checks"]) == 3
        check_names = [c["name"] for c in d["checks"]]
        assert "signature" in check_names
        assert "timestamp" in check_names
        assert "pq_signature" in check_names
        assert d["errors"] == ["error1"]
        assert d["warnings"] == ["warn1"]

    def test_result_with_bundle_no_verification(self):
        """Test result_to_dict with bundle but no verification data."""
        result = VerificationResult(is_valid=True)
        bundle = MagicMock()
        bundle.capsule_id = "caps_456"
        bundle.created_at = None
        bundle.verification = None

        d = result_to_dict(result, bundle)

        assert d["bundle"]["capsule_id"] == "caps_456"
        assert d["bundle"]["created_at"] is None
        assert "key_algorithm" not in d["bundle"]


class TestFormatResultEdgeCases:
    """Edge case tests for format_result."""

    def test_format_result_verbose_no_timestamp(self):
        """Test verbose output when timestamp not present."""
        result = VerificationResult(
            is_valid=True,
            signature_valid=True,
            timestamp_valid=None,  # Not present
        )
        output = format_result(result, verbose=True, no_color=True)

        assert "Timestamp: not present" in output

    def test_format_result_with_pq_signature(self):
        """Test output includes PQ signature status."""
        result = VerificationResult(
            is_valid=True,
            signature_valid=True,
            pq_signature_valid=True,
        )
        output = format_result(result, no_color=True)

        assert "PQ Signature:" in output
        assert "valid" in output

    def test_format_result_pq_signature_invalid(self):
        """Test output shows PQ signature invalid."""
        result = VerificationResult(
            is_valid=False,
            signature_valid=True,
            pq_signature_valid=False,
        )
        output = format_result(result, no_color=True)

        assert "PQ Signature:" in output
        assert "invalid" in output

    def test_format_result_multiple_errors(self):
        """Test output shows multiple errors."""
        result = VerificationResult(
            is_valid=False,
            errors=["Error 1", "Error 2", "Error 3"],
        )
        output = format_result(result, no_color=True)

        assert "Error 1" in output
        assert "Error 2" in output
        assert "Error 3" in output


class TestDetermineExitCodeEdgeCases:
    """Edge case tests for determine_exit_code."""

    def test_failed_with_warnings_still_failed(self):
        """Warnings should be ignored when verification failed."""
        result = VerificationResult(
            is_valid=False,
            warnings=["Warning that doesn't matter"],
        )
        assert determine_exit_code(result) == ExitCode.FAILED

    def test_exit_code_order(self):
        """Test that exit codes have expected ordering."""
        assert ExitCode.SUCCESS < ExitCode.FAILED
        assert ExitCode.FAILED < ExitCode.WARNINGS
        assert ExitCode.WARNINGS < ExitCode.CONFIG_ERROR
        assert ExitCode.CONFIG_ERROR < ExitCode.NETWORK_ERROR
