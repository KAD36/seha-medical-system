"""Runtime configuration for the Telegram bot.

Secrets are intentionally loaded from environment variables. Never commit a
real Telegram token or administrator ID to this repository.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "").strip()

API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    os.environ.get("RENDER_EXTERNAL_URL", "http://127.0.0.1:5000"),
).rstrip("/")
API_ENDPOINT = "/api/medical-leaves"
API_FULL_URL = f"{API_BASE_URL}{API_ENDPOINT}"

# The address printed in reports, embedded in their clickable link, and stored
# in their QR code must be the same public site.  Keep this separate from the
# API base so a local API can still be used while generating a test report.
PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    os.environ.get("RENDER_EXTERNAL_URL", API_BASE_URL),
).rstrip("/")

BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "fonts"
IMAGES_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR / "output"

NOTO_SANS_ARABIC_BOLD = str(FONTS_DIR / "noto_sans_arabic" / "NotoSansArabic-Bold.ttf")
NOTO_SANS_ARABIC_REGULAR = str(FONTS_DIR / "noto_sans_arabic" / "NotoSansArabic-Regular.ttf")
TIMES_NR_MT_BOLD = str(FONTS_DIR / "times_nr_mt" / "TimesNRMTPro-Bold.otf")
TIMES_NR_MT_REGULAR = str(FONTS_DIR / "times_nr_mt" / "TimesNRMTPro-Regular.otf")

SEHA_LOGO = str(IMAGES_DIR / "شعارصحةseha.jpg")
GEOMETRIC_SHAPE = str(IMAGES_DIR / "الشكلالهندسي.jpg")
KINGDOM_TEXT = str(IMAGES_DIR / "كلمةالمملكةالعربيةالسعوديةKingdomofSaudiArabia.jpg")
HOSPITAL_LOGO = str(IMAGES_DIR / "شعارالمستشفى.png")
HEALTH_INFO_CENTER_LOGO = str(IMAGES_DIR / "شعارالمركزالوطنيللمعلوماتالصحية.jpg")

# Backward-compatible name used by the PDF generators.
QR_URL = PUBLIC_SITE_URL

PDF_WIDTH = 297
PDF_HEIGHT = 419
