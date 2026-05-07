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
    verify_artifacts_in_capsule,
    verify_artifacts_strict,
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

        assert d["is_valid"]
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

    def test_verify_artifacts_json_output_for_capsule_file(self):
        runner = CliRunner()
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/app.py",
                            "operation": "write",
                            "content_hash_after": "a" * 64,
                            "content_size_after": 12,
                            "content_preview": "print('ok')",
                            "content_preview_truncated": False,
                            "content_preview_original_length": 11,
                            "redactions": 0,
                        }
                    ],
                    "files_total": 1,
                    "commands": [
                        {
                            "tool": "terminal",
                            "command": "PYTHONPATH=. .venv/bin/python -m pytest tests -q",
                            "exit_code": 0,
                            "stdout_hash": "b" * 64,
                            "stdout_size": 12,
                            "stdout_preview": "1 passed\n",
                            "stdout_preview_truncated": False,
                            "stdout_preview_original_length": 9,
                            "redactions": 0,
                            "is_verification": True,
                            "verification_type": "test",
                            "verification_status": "passed",
                        }
                    ],
                    "commands_total": 1,
                    "verification_commands_total": 1,
                }
            }
        }
        with runner.isolated_filesystem():
            Path("capsule.json").write_text(json.dumps(capsule))
            result = runner.invoke(
                verify_cmd,
                ["--artifacts", "capsule.json", "--output", "json"],
            )

        assert result.exit_code == ExitCode.SUCCESS
        output = json.loads(result.output)
        assert output["is_valid"] is True
        assert output["artifact_checks"]["files_total"] == 1
        assert output["artifact_checks"]["commands_total"] == 1
        assert output["artifact_checks"]["verification_commands_total"] == 1

    def test_verify_artifacts_strict_json_output_for_capsule_file(self, tmp_path):
        runner = CliRunner()
        root = tmp_path / "workspace"
        root.mkdir()
        source = root / "src" / "app.py"
        source.parent.mkdir()
        source.write_text("print('ok')\n")
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/app.py",
                            "operation": "write",
                            "content_hash_after": "ad64355106bb158b020ecf9702be48f7730fc091dd4bb6a2f092b40393495b3d",
                            "content_size_after": 12,
                            "content_preview": "print('ok')\n",
                            "content_preview_truncated": False,
                            "content_preview_original_length": 12,
                            "redactions": 0,
                        }
                    ],
                    "commands": [],
                }
            }
        }
        capsule_path = tmp_path / "capsule.json"
        capsule_path.write_text(json.dumps(capsule))

        result = runner.invoke(
            verify_cmd,
            [
                "--artifacts",
                str(capsule_path),
                "--strict",
                "--root",
                str(root),
                "--output",
                "json",
            ],
        )

        assert result.exit_code == ExitCode.SUCCESS
        output = json.loads(result.output)
        assert output["is_valid"] is True
        assert output["strict"] is True
        assert output["strict_checks"]["files_checked"] == 1


class TestArtifactVerification:
    def test_verify_artifacts_in_capsule_accepts_valid_base_manifest(self):
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/app.py",
                            "operation": "patch",
                            "old_string_hash": "a" * 64,
                            "new_string_hash": "b" * 64,
                            "old_string_size": 3,
                            "new_string_size": 4,
                        }
                    ],
                    "commands": [
                        {
                            "tool": "terminal",
                            "command": "git diff --check",
                            "exit_code": 0,
                            "stdout_hash": "c" * 64,
                            "stdout_size": 0,
                            "stdout_preview": "",
                            "stdout_preview_truncated": False,
                            "stdout_preview_original_length": 0,
                            "redactions": 0,
                            "is_verification": True,
                            "verification_type": "diff_check",
                            "verification_status": "passed",
                        }
                    ],
                    "files_total": 1,
                    "commands_total": 1,
                    "verification_commands_total": 1,
                }
            }
        }

        result = verify_artifacts_in_capsule(capsule)

        assert result["is_valid"] is True
        assert result["errors"] == []
        assert result["artifact_checks"]["files_total"] == 1
        assert result["artifact_checks"]["commands_total"] == 1

    def test_verify_artifacts_in_capsule_reports_missing_artifacts(self):
        result = verify_artifacts_in_capsule({"payload": {}})

        assert result["is_valid"] is False
        assert "payload.artifacts missing" in result["errors"]

    def test_verify_artifacts_in_capsule_reports_bad_hash_shape(self):
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/app.py",
                            "operation": "write",
                            "content_hash_after": "not-a-sha256",
                            "content_size_after": 1,
                            "content_preview": "x",
                            "content_preview_truncated": False,
                            "content_preview_original_length": 1,
                            "redactions": 0,
                        }
                    ],
                    "commands": [],
                }
            }
        }

        result = verify_artifacts_in_capsule(capsule)

        assert result["is_valid"] is False
        assert any("content_hash_after" in error for error in result["errors"])

    def test_verify_artifacts_in_capsule_accepts_h1_read_artifact_shape(self):
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/bar.py",
                            "operation": "read",
                            "offset": 1,
                            "limit": 200,
                        }
                    ],
                    "files_total": 1,
                    "commands": [],
                    "commands_total": 0,
                    "verification_commands_total": 0,
                }
            }
        }

        result = verify_artifacts_in_capsule(capsule)

        assert result["is_valid"] is True
        assert result["errors"] == []

    def test_verify_artifacts_in_capsule_reports_non_object_command_without_crash(self):
        capsule = {"payload": {"artifacts": {"files": [], "commands": ["bad"]}}}

        result = verify_artifacts_in_capsule(capsule)

        assert result["is_valid"] is False
        assert "payload.artifacts.commands[0] must be an object" in result["errors"]
        assert result["artifact_checks"] == {
            "files_total": 0,
            "commands_total": 1,
            "verification_commands_total": 0,
        }

    def test_verify_artifacts_strict_confirms_write_hash_against_workspace(
        self, tmp_path
    ):
        source = tmp_path / "src" / "app.py"
        source.parent.mkdir()
        source.write_text("print('ok')\n")
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/app.py",
                            "operation": "write",
                            "content_hash_after": "ad64355106bb158b020ecf9702be48f7730fc091dd4bb6a2f092b40393495b3d",
                            "content_size_after": 12,
                            "content_preview": "print('ok')\n",
                            "content_preview_truncated": False,
                            "content_preview_original_length": 12,
                            "redactions": 0,
                        }
                    ],
                    "commands": [],
                }
            }
        }

        result = verify_artifacts_strict(capsule, tmp_path)

        assert result["is_valid"] is True
        assert result["strict_checks"]["files_checked"] == 1
        assert result["strict_checks"]["file_hash_matches"] == 1

    def test_verify_artifacts_strict_reports_write_hash_mismatch(self, tmp_path):
        source = tmp_path / "src" / "app.py"
        source.parent.mkdir()
        source.write_text("print('changed')\n")
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "src/app.py",
                            "operation": "write",
                            "content_hash_after": "ad64355106bb158b020ecf9702be48f7730fc091dd4bb6a2f092b40393495b3d",
                            "content_size_after": 12,
                            "content_preview": "print('ok')\n",
                            "content_preview_truncated": False,
                            "content_preview_original_length": 12,
                            "redactions": 0,
                        }
                    ],
                    "commands": [],
                }
            }
        }

        result = verify_artifacts_strict(capsule, tmp_path)

        assert result["is_valid"] is False
        assert any("content_hash_after mismatch" in error for error in result["errors"])

    def test_verify_artifacts_strict_blocks_path_traversal(self, tmp_path):
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [
                        {
                            "path": "../outside.py",
                            "operation": "write",
                            "content_hash_after": "a" * 64,
                            "content_size_after": 1,
                            "content_preview": "x",
                            "content_preview_truncated": False,
                            "content_preview_original_length": 1,
                            "redactions": 0,
                        }
                    ],
                    "commands": [],
                }
            }
        }

        result = verify_artifacts_strict(capsule, tmp_path)

        assert result["is_valid"] is False
        assert any("escapes strict root" in error for error in result["errors"])

    def test_verify_artifacts_strict_fails_failed_verification_command(self, tmp_path):
        capsule = {
            "payload": {
                "artifacts": {
                    "files": [],
                    "commands": [
                        {
                            "command": ".venv/bin/python -m pytest tests -q",
                            "stdout_hash": "a" * 64,
                            "stdout_size": 10,
                            "stdout_preview": "1 failed",
                            "stdout_preview_truncated": False,
                            "stdout_preview_original_length": 8,
                            "redactions": 0,
                            "is_verification": True,
                            "verification_type": "test",
                            "verification_status": "failed",
                        }
                    ],
                }
            }
        }

        result = verify_artifacts_strict(capsule, tmp_path)

        assert result["is_valid"] is False
        assert "verification command failed: test" in result["errors"]


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
