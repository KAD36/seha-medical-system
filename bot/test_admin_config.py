#!/usr/bin/env python3
"""Regression tests for multi-admin configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import parse_admin_user_ids


def test_admin_ids_support_legacy_and_list_without_duplicates():
    assert parse_admin_user_ids("123", "123, 456;789") == ("123", "456", "789")


def test_admin_ids_ignore_invalid_values():
    assert parse_admin_user_ids("", "abc, 123-456, 987") == ("987",)
