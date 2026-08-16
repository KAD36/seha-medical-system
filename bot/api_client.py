#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Client used by the Telegram bot to save a leave in the Flask API."""

import logging
from datetime import datetime

import requests

from config import API_FULL_URL
from identifiers import generate_leave_id, normalize_identity


logger = logging.getLogger(__name__)


def calculate_days(admission_date, discharge_date):
    try:
        admission = datetime.strptime(admission_date, "%d-%m-%Y")
        discharge = datetime.strptime(discharge_date, "%d-%m-%Y")
        return max(1, (discharge - admission).days + 1)
    except (TypeError, ValueError):
        return 1


def _payload_from_user_data(user_data):
    admission_date = user_data.get("admission_date_gregorian", "")
    discharge_date = user_data.get("discharge_date_gregorian", "")
    leave_id = generate_leave_id(
        user_data.get("id_number", ""), admission_date, discharge_date
    )

    return leave_id, {
        "service_code": leave_id,
        "identity_number": normalize_identity(user_data.get("id_number", "")),
        "patient_name_ar": user_data.get("patient_name_ar", ""),
        "patient_name_en": user_data.get("patient_name_en", ""),
        "nationality_ar": user_data.get("nationality_ar", ""),
        "nationality_en": user_data.get("nationality_en", ""),
        "workplace_ar": user_data.get("employer_ar", ""),
        "workplace_en": user_data.get("employer_en", ""),
        "doctor_name_ar": user_data.get("doctor_name_ar", ""),
        "doctor_name_en": user_data.get("doctor_name_en", ""),
        "job_title_ar": user_data.get("position_ar", ""),
        "job_title_en": user_data.get("position_en", ""),
        "admission_date_gregorian": admission_date,
        "admission_date_hijri": user_data.get("admission_date_hijri", ""),
        "discharge_date_gregorian": discharge_date,
        "discharge_date_hijri": user_data.get("discharge_date_hijri", ""),
        "report_issue_date": user_data.get(
            "issue_date_gregorian", discharge_date
        ),
        "facility_name_ar": user_data.get("hospital_name_ar", ""),
        "facility_name_en": user_data.get("hospital_name_en", ""),
        "report_time": user_data.get("time", ""),
        "duration_days": calculate_days(admission_date, discharge_date),
    }


def send_leave_data_to_api(user_data):
    leave_id, payload = _payload_from_user_data(user_data)

    try:
        logger.info("Sending leave data to the configured API")
        response = requests.post(API_FULL_URL, json=payload, timeout=60)

        if response.status_code in (200, 201):
            result = response.json()
            # A successful write is not enough: verify that the exact pair
            # printed in the report is immediately searchable.
            search_response = requests.post(
                f"{API_FULL_URL}/search",
                json={
                    "service_code": leave_id,
                    "identity_number": payload["identity_number"],
                },
                timeout=60,
            )
            try:
                search_result = search_response.json()
            except ValueError:
                search_result = {}
            if search_response.status_code != 200 or not search_result.get("found"):
                logger.error("Saved leave could not be verified by inquiry endpoint")
                return {
                    "success": False,
                    "message": "تم الإرسال لكن تعذر التحقق من ظهوره في الاستعلام",
                    "leave_id": leave_id,
                }
            return {
                "success": True,
                "message": result.get("message", "Saved successfully"),
                "leave_id": leave_id,
                "identity_number": payload["identity_number"],
                "data": result,
            }

        try:
            result = response.json()
            message = result.get("error") or result.get("message")
        except ValueError:
            message = None

        logger.error("API returned HTTP %s", response.status_code)
        return {
            "success": False,
            "message": message or f"HTTP {response.status_code}",
            "leave_id": leave_id,
        }
    except requests.exceptions.ConnectionError:
        message = "تعذر الاتصال بالموقع. تأكد من API_BASE_URL وتشغيل الموقع."
    except requests.exceptions.Timeout:
        message = "انتهت مهلة الاتصال بالموقع."
    except Exception as exc:
        logger.exception("Unexpected API client error")
        message = f"خطأ غير متوقع: {exc}"

    return {"success": False, "message": message, "leave_id": leave_id}


if __name__ == "__main__":
    raise SystemExit("Import this module from the bot; it is not a standalone command.")
