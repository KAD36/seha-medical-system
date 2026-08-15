"""
نموذج قاعدة البيانات للإجازات المرضية
Medical Leave Database Model
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

class MedicalLeave:
    def __init__(self, db_path: str = "src/database/app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جدول الإجازات المرضية إذا لم يكن موجوداً"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medical_leaves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_code TEXT NOT NULL UNIQUE,
                    identity_number TEXT NOT NULL,
                    patient_name_ar TEXT NOT NULL,
                    patient_name_en TEXT NOT NULL,
                    nationality_ar TEXT NOT NULL,
                    nationality_en TEXT NOT NULL,
                    workplace_ar TEXT NOT NULL,
                    workplace_en TEXT NOT NULL,
                    doctor_name_ar TEXT NOT NULL,
                    doctor_name_en TEXT NOT NULL,
                    job_title_ar TEXT NOT NULL,
                    job_title_en TEXT NOT NULL,
                    admission_date_gregorian TEXT NOT NULL,
                    admission_date_hijri TEXT NOT NULL,
                    discharge_date_gregorian TEXT NOT NULL,
                    discharge_date_hijri TEXT NOT NULL,
                    report_issue_date TEXT NOT NULL,
                    facility_name_ar TEXT NOT NULL,
                    facility_name_en TEXT NOT NULL,
                    report_time TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء فهارس للبحث السريع
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_code ON medical_leaves(service_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_identity_number ON medical_leaves(identity_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_identity ON medical_leaves(service_code, identity_number)')
            
            conn.commit()
    
    def create_medical_leave(self, data: Dict[str, Any]) -> bool:
        """إنشاء إجازة مرضية جديدة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO medical_leaves (
                        service_code, identity_number, patient_name_ar, patient_name_en,
                        nationality_ar, nationality_en, workplace_ar, workplace_en,
                        doctor_name_ar, doctor_name_en, job_title_ar, job_title_en,
                        admission_date_gregorian, admission_date_hijri, discharge_date_gregorian, discharge_date_hijri,
                        report_issue_date, facility_name_ar, facility_name_en, report_time, duration_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['service_code'], data['identity_number'], data['patient_name_ar'], data['patient_name_en'],
                    data['nationality_ar'], data['nationality_en'], data['workplace_ar'], data['workplace_en'],
                    data['doctor_name_ar'], data['doctor_name_en'], data['job_title_ar'], data['job_title_en'],
                    data['admission_date_gregorian'], data['admission_date_hijri'], 
                    data['discharge_date_gregorian'], data['discharge_date_hijri'],
                    data['report_issue_date'], data['facility_name_ar'], data['facility_name_en'], 
                    data['report_time'], data['duration_days']
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"خطأ في إنشاء الإجازة المرضية: {e}")
            return False
    
    def get_medical_leave_by_service_and_identity(self, service_code: str, identity_number: str) -> Optional[Dict[str, Any]]:
        """البحث عن إجازة مرضية برمز الخدمة ورقم الهوية"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM medical_leaves 
                    WHERE service_code = ? AND identity_number = ?
                ''', (service_code, identity_number))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            print(f"خطأ في البحث عن الإجازة المرضية: {e}")
            return None
    
    def get_all_medical_leaves(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الإجازات المرضية"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM medical_leaves ORDER BY created_at DESC')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"خطأ في الحصول على الإجازات المرضية: {e}")
            return []
    
    def update_medical_leave(self, service_code: str, data: Dict[str, Any]) -> bool:
        """تحديث إجازة مرضية موجودة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE medical_leaves SET
                        identity_number = ?, patient_name_ar = ?, patient_name_en = ?,
                        nationality_ar = ?, nationality_en = ?, workplace_ar = ?, workplace_en = ?,
                        doctor_name_ar = ?, doctor_name_en = ?, job_title_ar = ?, job_title_en = ?,
                        admission_date_gregorian = ?, admission_date_hijri = ?, 
                        discharge_date_gregorian = ?, discharge_date_hijri = ?,
                        report_issue_date = ?, facility_name_ar = ?, facility_name_en = ?, 
                        report_time = ?, duration_days = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE service_code = ?
                ''', (
                    data['identity_number'], data['patient_name_ar'], data['patient_name_en'],
                    data['nationality_ar'], data['nationality_en'], data['workplace_ar'], data['workplace_en'],
                    data['doctor_name_ar'], data['doctor_name_en'], data['job_title_ar'], data['job_title_en'],
                    data['admission_date_gregorian'], data['admission_date_hijri'], 
                    data['discharge_date_gregorian'], data['discharge_date_hijri'],
                    data['report_issue_date'], data['facility_name_ar'], data['facility_name_en'], 
                    data['report_time'], data['duration_days'], service_code
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"خطأ في تحديث الإجازة المرضية: {e}")
            return False
    
    def delete_medical_leave(self, service_code: str) -> bool:
        """حذف إجازة مرضية"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM medical_leaves WHERE service_code = ?', (service_code,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"خطأ في حذف الإجازة المرضية: {e}")
            return False
