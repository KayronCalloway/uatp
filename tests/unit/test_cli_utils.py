"""
Unit tests for CLI utility functions.
"""

import pytest

from src.cli.inspect import format_bytes, print_tree


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_bytes_small(self):
        """Test formatting small byte values."""
        assert format_bytes(0) == "0.0 B"
        assert format_bytes(1) == "1.0 B"
        assert format_bytes(512) == "512.0 B"
        assert format_bytes(1023) == "1023.0 B"

    def test_kilobytes(self):
        """Test formatting kilobyte values."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(10240) == "10.0 KB"

    def test_megabytes(self):
        """Test formatting megabyte values."""
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 5) == "5.0 MB"
        assert format_bytes(1024 * 1024 * 100) == "100.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabyte values."""
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
        assert format_bytes(1024 * 1024 * 1024 * 2) == "2.0 GB"

    def test_terabytes(self):
        """Test formatting terabyte values."""
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1.0 TB"
        assert format_bytes(1024 * 1024 * 1024 * 1024 * 3) == "3.0 TB"


class TestPrintTree:
    """Tests for print_tree function."""

    def test_simple_dict(self, capsys):
        """Test printing simple dict."""
        data = {"key": "value"}
        print_tree(data)
        captured = capsys.readouterr()
        assert "key" in captured.out
        assert "value" in captured.out

    def test_nested_dict(self, capsys):
        """Test printing nested dict."""
        data = {"outer": {"inner": "value"}}
        print_tree(data)
        captured = capsys.readouterr()
        assert "outer" in captured.out
        assert "inner" in captured.out

    def test_list_values(self, capsys):
        """Test printing list values."""
        data = {"items": ["a", "b", "c"]}
        print_tree(data)
        captured = capsys.readouterr()
        assert "items" in captured.out
        assert "[3 items]" in captured.out

    def test_long_list_truncated(self, capsys):
        """Test that long lists show truncation message."""
        data = {"items": ["a", "b", "c", "d", "e"]}
        print_tree(data)
        captured = capsys.readouterr()
        assert "and 2 more" in captured.out

    def test_long_string_truncated(self, capsys):
        """Test that long strings are truncated."""
        data = {"content": "x" * 100}
        print_tree(data)
        captured = capsys.readouterr()
        assert "..." in captured.out
        # Should not contain full string
        assert "x" * 100 not in captured.out
