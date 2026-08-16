#!/usr/bin/env python3
"""Regression tests for facility/doctor and nationality catalog behavior."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog import (
    DOCTORS,
    FACILITY_DOCTORS,
    FACILITY_DOCTOR_SOURCES,
    doctor_labels_for_facility,
    nationality_pair,
)
from message_parser import MessageParser


def test_saudi_is_default_translation():
    assert nationality_pair("سعودي") == ("سعودي", "Saudi Arabia")
    assert nationality_pair("سعودية") == ("سعودي", "Saudi Arabia")
    assert nationality_pair("المملكة العربية السعودية") == ("سعودي", "Saudi Arabia")


def test_common_arabic_nationalities_translate_automatically():
    assert nationality_pair("مصرية") == ("مصري", "Egyptian")
    assert nationality_pair("باكستان") == ("باكستاني", "Pakistani")
    assert nationality_pair("إندونيسية") == ("إندونيسي", "Indonesian")
    assert nationality_pair("إريترية") == ("إريتري", "Eritrean")


def test_unknown_nationality_requires_manual_english():
    assert nationality_pair("جنسية غير مدرجة") is None


def test_only_verified_doctors_are_shown_for_a_facility():
    labels = doctor_labels_for_facility("السعودي الالماني الصحي")
    assert labels == ["خالد علي العنزي - استشاري الطب الباطني"]
    assert DOCTORS[labels[0]][2:] == (
        "استشاري الطب الباطني",
        "Internal Medicine Consultant",
    )


def test_unverified_facility_does_not_receive_generic_doctors():
    assert doctor_labels_for_facility("مستشفى عسير المركزي") == []


def test_every_facility_relationship_has_a_doctor_and_source():
    saved_doctor_names = {record[0] for record in DOCTORS.values()}
    for facility, doctor_names in FACILITY_DOCTORS.items():
        for doctor_name in doctor_names:
            assert doctor_name in saved_doctor_names
            assert FACILITY_DOCTOR_SOURCES[(facility, doctor_name)].startswith("https://")


def test_formatted_message_replaces_stale_english_nationality():
    data = MessageParser().validate_data({
        "nationality_ar": "مصرية",
        "nationality_en": "Saudi Arabia",
    })
    assert data["nationality_ar"] == "مصري"
    assert data["nationality_en"] == "Egyptian"
