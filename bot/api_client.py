#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Client for Seha Website Integration
عميل API لربط البوت بموقع صحة
"""

import requests
import json
import logging
from datetime import datetime
from config import API_FULL_URL

# إعداد التسجيل
logger = logging.getLogger(__name__)

def calculate_days(admission_date, discharge_date):
    """حساب عدد الأيام بين تاريخين"""
    try:
        # تحويل التواريخ من صيغة dd-mm-yyyy إلى datetime
        admission_parts = admission_date.split('-')
        discharge_parts = discharge_date.split('-')
        
        if len(admission_parts) == 3 and len(discharge_parts) == 3:
            admission_dt = datetime(int(admission_parts[2]), int(admission_parts[1]), int(admission_parts[0]))
            discharge_dt = datetime(int(discharge_parts[2]), int(discharge_parts[1]), int(discharge_parts[0]))
            
            days = (discharge_dt - admission_dt).days + 1
            return max(1, days)  # على الأقل يوم واحد
        else:
            return 1
    except Exception as e:
        logger.error(f"خطأ في حساب الأيام: {e}")
        return 1

def generate_leave_id(id_number, admission_date, discharge_date):
    """توليد رمز الإجازة مطابق لما يتم في PDF"""
    try:
        # PSL + رقم مكون من رقم الهوية وتاريخ الدخول والخروج (11 رقم)
        id_part = id_number[-4:] if len(id_number) >= 4 else id_number
        
        # استخراج الأرقام من التواريخ
        admission_nums = ''.join(filter(str.isdigit, admission_date))[-3:]
        discharge_nums = ''.join(filter(str.isdigit, discharge_date))[-4:]
        
        # تكوين الرقم (11 رقم)
        leave_number = (id_part + admission_nums + discharge_nums).ljust(11, '0')[:11]
        
        return f"PSL{leave_number}"
    except Exception as e:
        logger.error(f"خطأ في توليد رمز الإجازة: {e}")
        return f"PSL{id_number[-4:] if len(id_number) >= 4 else id_number}0000000"

def convert_date_format(date_str):
    """تحويل التاريخ من صيغة dd-mm-yyyy إلى yyyy-mm-dd"""
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return date_str
    except:
        return date_str

def send_leave_data_to_api(user_data):
    """إرسال بيانات الإجازة إلى API الموقع"""
    try:
        # توليد رمز الإجازة
        leave_id = generate_leave_id(
            user_data.get('id_number', ''),
            user_data.get('admission_date_gregorian', ''),
            user_data.get('discharge_date_gregorian', '')
        )
        
        # تحويل التواريخ إلى الصيغة المطلوبة
        report_date = convert_date_format(user_data.get('issue_date_gregorian', ''))
        entry_date = convert_date_format(user_data.get('admission_date_gregorian', ''))
        exit_date = convert_date_format(user_data.get('discharge_date_gregorian', ''))
        
        # إعداد البيانات للإرسال
        api_data = {
            'leaveNumber': leave_id,
            'idNumber': user_data.get('id_number', ''),
            'name': user_data.get('patient_name_ar', ''),
            'reportDate': report_date,
            'entryDate': entry_date,
            'exitDate': exit_date,
            'doctor': user_data.get('doctor_name_ar', ''),
            'jobTitle': user_data.get('position_ar', '')
        }
        
        # إرسال البيانات
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'
        }
        
        logger.info(f"إرسال البيانات إلى API: {API_FULL_URL}")
        logger.info(f"البيانات المرسلة: {json.dumps(api_data, ensure_ascii=False)}")
        
        response = requests.post(
            API_FULL_URL,
            json=api_data,
            headers=headers,
            timeout=30
        )
        
        # التحقق من الاستجابة
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"تم إرسال البيانات بنجاح: {result.get('message')}")
                return {
                    'success': True,
                    'message': 'تم حفظ بيانات الإجازة في النظام بنجاح',
                    'leave_id': leave_id,
                    'data': result.get('data', {})
                }
            else:
                logger.error(f"فشل في حفظ البيانات: {result.get('message')}")
                return {
                    'success': False,
                    'message': f"فشل في حفظ البيانات: {result.get('message')}",
                    'leave_id': leave_id
                }
        else:
            logger.error(f"خطأ HTTP {response.status_code}: {response.text}")
            return {
                'success': False,
                'message': f"خطأ في الاتصال بالخادم (HTTP {response.status_code})",
                'leave_id': leave_id
            }
            
    except requests.exceptions.ConnectionError:
        logger.error("فشل في الاتصال بالخادم")
        return {
            'success': False,
            'message': 'فشل في الاتصال بالخادم. تأكد من تشغيل الموقع.',
            'leave_id': leave_id if 'leave_id' in locals() else 'غير محدد'
        }
    except requests.exceptions.Timeout:
        logger.error("انتهت مهلة الاتصال")
        return {
            'success': False,
            'message': 'انتهت مهلة الاتصال بالخادم',
            'leave_id': leave_id if 'leave_id' in locals() else 'غير محدد'
        }
    except Exception as e:
        logger.error(f"خطأ غير متوقع في إرسال البيانات: {e}")
        return {
            'success': False,
            'message': f'خطأ غير متوقع: {str(e)}',
            'leave_id': leave_id if 'leave_id' in locals() else 'غير محدد'
        }

if __name__ == "__main__":
    # اختبار سريع
    test_data = {
        'id_number': '1234567890',
        'patient_name_ar': 'أحمد محمد السعيد',
        'issue_date_gregorian': '20-01-2025',
        'admission_date_gregorian': '18-01-2025',
        'discharge_date_gregorian': '20-01-2025',
        'doctor_name_ar': 'د. نبيل حنا نصر',
        'position_ar': 'طبيب عام'
    }
    
    result = send_leave_data_to_api(test_data)
    print(f"نتيجة الاختبار: {json.dumps(result, ensure_ascii=False, indent=2)}")

