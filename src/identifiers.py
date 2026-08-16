"""Canonical normalization used by the public inquiry API."""

import re


_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)


def normalize_digits(value) -> str:
    return str(value or "").translate(_DIGIT_TRANSLATION)


def normalize_identity(value) -> str:
    return re.sub(r"\D", "", normalize_digits(value))


def normalize_service_code(value) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_digits(value).upper())
