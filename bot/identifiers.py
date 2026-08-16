"""Canonical formatting for report identifiers shared by bot and PDF."""

import re


_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)


def normalize_digits(value) -> str:
    return str(value or "").translate(_DIGIT_TRANSLATION)


def normalize_identity(value) -> str:
    """Return a digits-only identity number using Western digits."""
    return re.sub(r"\D", "", normalize_digits(value))


def normalize_service_code(value) -> str:
    """Normalize pasted service codes regardless of spaces or letter case."""
    return re.sub(r"[^A-Z0-9]", "", normalize_digits(value).upper())


def generate_leave_id(id_number, admission_date, discharge_date) -> str:
    identity = normalize_identity(id_number)
    admission = normalize_digits(admission_date)
    discharge = normalize_digits(discharge_date)
    id_part = identity[-4:] if len(identity) >= 4 else identity
    admission_nums = re.sub(r"\D", "", admission)[-3:]
    discharge_nums = re.sub(r"\D", "", discharge)[-4:]
    leave_number = (id_part + admission_nums + discharge_nums).ljust(11, "0")[:11]
    return f"PSL{leave_number}"
