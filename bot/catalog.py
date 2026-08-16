"""Curated doctor/facility choices recovered from the project's source data."""

import re
import unicodedata
from pathlib import Path


CUSTOM_ENTRY = "✍️ إدخال اسم آخر"
DEFAULT_NATIONALITY_BUTTON = "🇸🇦 سعودي (الافتراضي)"
OTHER_NATIONALITY_BUTTON = "✍️ جنسية أخرى"
LOGOS_DIR = Path(__file__).resolve().parent / "facility_logos"


DOCTORS = {
    "محمد راشد السر - استشاري": ("محمد راشد السر", "MUHAMMAD RASHID AL-SIR", "استشاري", "Consultant"),
    "صالح عبدالوهاب عوض سليمان - طبيب عام": ("صالح عبدالوهاب عوض سليمان", "SALEH ABDLWAHAB AWAD SLEMAN", "طبيب عام", "General Practitioner"),
    "حسن ضيف الله الفاضل - استشاري": ("حسن ضيف الله الفاضل", "HASAN DAYF ALLAH ALFADIL", "استشاري", "Consultant"),
    "عبدالله مفرح علي عسير - طبيب عام": ("عبدالله مفرح علي عسير", "ABDULLAH MUFRAH ALI ASIR", "طبيب عام", "General Practitioner"),
    "عبدالله محمد العمري - استشاري": ("عبدالله محمد العمري", "ABDULLAH MOHAMMED AL-OMARI", "استشاري", "Consultant"),
    "خالد علي العنزي - استشاري الطب الباطني": ("خالد علي العنزي", "KHALID ALI AL-ANZI", "استشاري الطب الباطني", "Internal Medicine Consultant"),
    "احمد اسامة ابوالعينين - استشاري": ("احمد اسامة ابوالعينين", "AHMED OSAMA ABU ALAYNIN", "استشاري", "Consultant"),
    "فيصل وليد غالب شهوان - استشاري": ("فيصل وليد غالب شهوان", "FAISAL WALID GHALIB SHAHWAN", "استشاري", "Consultant"),
    "محمد الكاف - استشاري": ("محمد الكاف", "MUHAMMAD AL-KAF", "استشاري", "Consultant"),
    "احمد العنزي - استشاري": ("احمد العنزي", "AHMAD AL-ANZI", "استشاري", "Consultant"),
    "يوسف العمري - استشاري": ("يوسف العمري", "YOUSSEF AL OMARI", "استشاري", "Consultant"),
    "محمد سليمان البشير - استشاري": ("محمد سليمان البشير", "MUHAMMAD SULEIMAN AL-BASHIR", "استشاري", "Consultant"),
    "مهدي الجارودي - استشاري": ("مهدي الجارودي", "MAHDI AL-JAROUDI", "استشاري", "Consultant"),
    "اماني الحربي - استشاري": ("اماني الحربي", "AMANI AL-HARBI", "استشاري", "Consultant"),
    "سعود رخيص خليف العنزي - طبيب عام": ("سعود رخيص خليف العنزي", "SAUD RKHIYES KH ALANAZI", "طبيب عام", "General Practitioner"),
    "الاء علي الحارثي - طب الاسنان": ("الاء علي الحارثي", "ALAA ALI AL HARITHI", "طب الاسنان والتخصصات المساندة", "Dentistry and Related Specialties"),
    "جمال راشد السر - استشاري": ("جمال راشد السر", "JAMAL RASHID AL SIR", "استشاري", "Consultant"),
    "مصباح عباس الحنبلي - استشاري": ("مصباح عباس الحنبلي", "MISBAH ABBAS AL HANBALI", "استشاري", "Consultant"),
    "محمد الصياد - استشاري": ("محمد الصياد", "MOHAMMED AL SAYYAD", "استشاري", "Consultant"),
}


# Arabic name: (English name, source logo number)
FACILITIES = {
    "المركز السعودي الطبي": ("Saudi Medical Center", 1),
    "مستشفى الملك فهد العام": ("King Fahd General Hospital", 1),
    "مستشفى الملك عبدالعزيز العام": ("King Abdulaziz General Hospital", 1),
    "مستشفى الملك سعود العام": ("King Saud General Hospital", 1),
    "مستشفى الملك خالد العام": ("King Khalid General Hospital", 1),
    "مستشفى الملك سلمان العام": ("King Salman General Hospital", 1),
    "مستشفى الملك فهد التخصصي": ("King Fahd Specialist Hospital", 1),
    "مستشفى الملك عبدالعزيز التخصصي": ("King Abdulaziz Specialist Hospital", 1),
    "مستشفى الملك سعود التخصصي": ("King Saud Specialist Hospital", 1),
    "مستشفى الملك خالد التخصصي": ("King Khalid Specialist Hospital", 1),
    "مستشفى الملك سلمان التخصصي": ("King Salman Specialist Hospital", 1),
    "مستشفى الملك عبدالله التخصصي": ("King Abdullah Specialist Hospital", 1),
    "مستشفى الملك فهد الجامعي": ("King Fahd University Hospital", 1),
    "مستشفى الصادق": ("Al-Sadiq Hospital", 2),
    "مستشفى الأمير سلطان": ("Prince Sultan Hospital", 1),
    "مستشفى خميس مشيط العام": ("Khamis Mushait General Hospital", 1),
    "مستشفى الخفجي العام": ("Al-Khafji General Hospital", 1),
    "مستشفى جازان العام": ("Jazan General Hospital", 1),
    "مستشفى عسير المركزي": ("Asir Central Hospital", 14),
    "مستشفى الدمام المركزي": ("Dammam Central Hospital", 1),
    "مستشفى حراء العام": ("Hiraa General Hospital", 1),
    "مستشفى القصيم الوطني": ("Al Qassim National Hospital", 4),
    "مجمع رهف الطبي": ("Rahaf Medical Complex", 3),
    "مستشفى الحياة الوطني": ("Hayat National Hospital", 6),
    "مجمع الدمام الاهلي": ("Dammam National Medical Complex", 7),
    "مستشفى الظافر بنجران": ("Alzafer Hospital Najran", 8),
    "مدينة الملك سعود الطبية": ("King Saud Medical City", 9),
    "مدينة الملك عبدالله الطبية": ("King Abdullah Medical City", 10),
    "مستشفى القوات المسلحة": ("Armed Forces Hospital", 5),
    "مستشفى الامير منصور العسكري": ("Prince Mansour Military Hospital", 5),
    "مستشفى النماص العام": ("Al-Namas General Hospital", 11),
    "مجمع العالمي الطبي": ("Al Alami Medical Complex", 12),
    "مجمع العائلة الطبي": ("Family Medical Complex", 13),
    "مستشفى الملك خالد بالخبر": ("King Khalid Hospital in AlKhobar", 1),
    "مستشفى محايل عسير العام": ("Mahayil Asir General Hospital", 1),
    "مستشفى قنفذة العام": ("Qunfudhah General Hospital", 1),
    "مجمع الدمام الطبي": ("Dammam Medical Complex", 18),
    "مستشفى دلة الصحي": ("Dallah Health Hospital", 16),
    "مستشفى د.سليمان حبيب": ("Dr. Sulaiman Habib Hospital", 15),
    "السعودي الالماني الصحي": ("Saudi German Health", 17),
    "مستشفى عرعر المركزي": ("Arar Central Hospital", 1),
    "مستشفى رفحاء المركزي": ("Rafha Central Hospital", 20),
    "مستشفى شقراء العام": ("Shaqra General Hospital", 19),
    "مستشفى ضباء العام": ("Duba General Hospital", 1),
    "العيادات المتقدمة الاستشارية": ("Advanced Consulting Clinics", 21),
    "مستشفى الامير محمد بن عبدالعزيز": ("Prince Mohammed Bin Abdulaziz Hospital", 1),
    "مستشفى صبيا العام": ("Sabia General Hospital", 1),
}

POSITIONS = {
    "استشاري": "Consultant",
    "استشاري الطب الباطني": "Internal Medicine Consultant",
    "طبيب عام": "General Practitioner",
    "طب الاسنان": "Dentistry",
    "طب الأسنان": "Dentistry",
    "طب الاسنان والتخصصات المساندة": "Dentistry and Related Specialties",
    "طب الأسنان والتخصصات المساندة": "Dentistry and Related Specialties",
}

# Only current relationships confirmed by an official facility directory belong
# here. The remaining recovered names stay available for formatted legacy input,
# but are not attributed to a facility based on name similarity.
FACILITY_DOCTORS = {
    "السعودي الالماني الصحي": ("خالد علي العنزي",),
}

# Public source used to verify each relationship above (reviewed 2026-08-16).
FACILITY_DOCTOR_SOURCES = {
    ("السعودي الالماني الصحي", "خالد علي العنزي"):
        "https://riyadh.saudigermanhealth.com/ar/doctor/د-خالد-علي-العنزي",
}


_NATIONALITY_RECORDS = {
    "سعودي": ("سعودي", "Saudi Arabia"),
    "السعودية": ("سعودي", "Saudi Arabia"),
    "مصري": ("مصري", "Egyptian"),
    "يمني": ("يمني", "Yemeni"),
    "سوداني": ("سوداني", "Sudanese"),
    "سوري": ("سوري", "Syrian"),
    "اردني": ("أردني", "Jordanian"),
    "فلسطيني": ("فلسطيني", "Palestinian"),
    "لبناني": ("لبناني", "Lebanese"),
    "عراقي": ("عراقي", "Iraqi"),
    "كويتي": ("كويتي", "Kuwaiti"),
    "بحريني": ("بحريني", "Bahraini"),
    "قطري": ("قطري", "Qatari"),
    "اماراتي": ("إماراتي", "Emirati"),
    "عماني": ("عُماني", "Omani"),
    "مغربي": ("مغربي", "Moroccan"),
    "جزائري": ("جزائري", "Algerian"),
    "تونسي": ("تونسي", "Tunisian"),
    "ليبي": ("ليبي", "Libyan"),
    "موريتاني": ("موريتاني", "Mauritanian"),
    "صومالي": ("صومالي", "Somali"),
    "جيبوتي": ("جيبوتي", "Djiboutian"),
    "باكستاني": ("باكستاني", "Pakistani"),
    "هندي": ("هندي", "Indian"),
    "بنغلاديشي": ("بنغلاديشي", "Bangladeshi"),
    "فلبيني": ("فلبيني", "Filipino"),
    "اندونيسي": ("إندونيسي", "Indonesian"),
    "اثيوبي": ("إثيوبي", "Ethiopian"),
    "اريتري": ("إريتري", "Eritrean"),
    "تركي": ("تركي", "Turkish"),
    "افغاني": ("أفغاني", "Afghan"),
    "نيبالي": ("نيبالي", "Nepalese"),
    "سريلانكي": ("سريلانكي", "Sri Lankan"),
}

_NATIONALITY_ALIASES = {
    "المملكة العربية السعودية": "سعودي", "السعودية": "سعودي",
    "سعودية": "سعودي", "سعوديه": "سعودي",
    "مصر": "مصري",
    "مصرية": "مصري", "مصريه": "مصري",
    "اليمن": "يمني",
    "يمنية": "يمني", "يمنيه": "يمني",
    "السودان": "سوداني",
    "سودانية": "سوداني", "سودانيه": "سوداني",
    "سوريا": "سوري",
    "سورية": "سوري", "سوريه": "سوري",
    "الاردن": "اردني",
    "اردنية": "اردني", "اردنيه": "اردني",
    "فلسطين": "فلسطيني",
    "فلسطينية": "فلسطيني", "فلسطينيه": "فلسطيني",
    "لبنان": "لبناني",
    "لبنانية": "لبناني", "لبنانيه": "لبناني",
    "العراق": "عراقي",
    "عراقية": "عراقي", "عراقيه": "عراقي",
    "الكويت": "كويتي",
    "كويتية": "كويتي", "كويتيه": "كويتي",
    "البحرين": "بحريني",
    "بحرينية": "بحريني", "بحرينيه": "بحريني",
    "قطر": "قطري",
    "قطرية": "قطري", "قطريه": "قطري",
    "الامارات": "اماراتي", "الامارات العربية المتحدة": "اماراتي",
    "اماراتية": "اماراتي", "اماراتيه": "اماراتي",
    "عمان": "عماني", "سلطنة عمان": "عماني",
    "عمانية": "عماني", "عمانيه": "عماني",
    "المغرب": "مغربي",
    "مغربية": "مغربي", "مغربيه": "مغربي",
    "الجزائر": "جزائري",
    "جزائرية": "جزائري", "جزائريه": "جزائري",
    "تونس": "تونسي",
    "تونسية": "تونسي", "تونسيه": "تونسي",
    "ليبيا": "ليبي",
    "ليبية": "ليبي", "ليبيه": "ليبي",
    "موريتانيا": "موريتاني", "موريتانية": "موريتاني", "موريتانيه": "موريتاني",
    "الصومال": "صومالي", "صومالية": "صومالي", "صوماليه": "صومالي",
    "جيبوتية": "جيبوتي", "جيبوتيه": "جيبوتي",
    "باكستان": "باكستاني",
    "باكستانية": "باكستاني", "باكستانيه": "باكستاني",
    "الهند": "هندي",
    "هندية": "هندي", "هنديه": "هندي",
    "بنغلاديش": "بنغلاديشي", "بنغلاديشية": "بنغلاديشي", "بنغلاديشيه": "بنغلاديشي",
    "الفلبين": "فلبيني",
    "فلبينية": "فلبيني", "فلبينيه": "فلبيني",
    "اندونيسيا": "اندونيسي",
    "اندونيسية": "اندونيسي", "اندونيسيه": "اندونيسي",
    "اثيوبيا": "اثيوبي",
    "اثيوبية": "اثيوبي", "اثيوبيه": "اثيوبي",
    "اريتريا": "اريتري", "اريترية": "اريتري", "اريتريه": "اريتري",
    "تركيا": "تركي",
    "تركية": "تركي", "تركيه": "تركي",
    "افغانستان": "افغاني", "افغانية": "افغاني", "افغانيه": "افغاني",
    "نيبال": "نيبالي", "نيبالية": "نيبالي", "نيباليه": "نيبالي",
    "سريلانكا": "سريلانكي", "سريلانكية": "سريلانكي", "سريلانكيه": "سريلانكي",
}


_LETTERS = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "aa", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "th", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "a",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "ة": "ah", "و": "w", "ؤ": "o", "ي": "y", "ى": "a", "ئ": "e", "ء": "",
}


def normalize_arabic(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    return re.sub(r"\s+", " ", text)


def nationality_pair(arabic: str):
    """Return a reviewed Arabic/English nationality pair, if recognized."""
    value = normalize_arabic(arabic)
    key = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ؤ", "و")
    key = _NATIONALITY_ALIASES.get(key, key)
    return _NATIONALITY_RECORDS.get(key)


def automatic_english(arabic: str, *, doctor: bool = False) -> str:
    value = re.sub(r"^(الدكتور|الدكتورة|د\.)\s*", "", normalize_arabic(arabic))
    words = []
    for word in value.split():
        prefix = "Al-" if word.startswith("ال") and len(word) > 2 else ""
        core = word[2:] if prefix else word
        rendered = "".join(_LETTERS.get(char, char) for char in core)
        rendered = re.sub(r"[^A-Za-z0-9-]", "", rendered)
        words.append(prefix + rendered.capitalize())
    result = " ".join(filter(None, words))
    return f"Dr. {result}" if doctor else result


def doctor_keyboard_rows():
    return [[label] for label in DOCTORS] + [[CUSTOM_ENTRY]]


def facility_keyboard_rows():
    return [[name] for name in FACILITIES] + [[CUSTOM_ENTRY]]


def facility_logo_path(arabic_name: str) -> str:
    record = FACILITIES.get(normalize_arabic(arabic_name))
    return str(LOGOS_DIR / f"{record[1]}.jpg") if record else ""


def doctor_labels_for_facility(arabic_name: str):
    doctor_names = FACILITY_DOCTORS.get(normalize_arabic(arabic_name), ())
    allowed = set(doctor_names)
    return [label for label, doctor in DOCTORS.items() if doctor[0] in allowed]
