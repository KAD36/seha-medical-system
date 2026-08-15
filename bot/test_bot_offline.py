#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline Test for Seha Sick Leave Bot
اختبار البوت بدون الاتصال بتيليجرام
"""

from pdf_generator_v4 import generate_sick_leave_pdf
import os

def test_pdf_generation():
    """اختبار توليد ملفات PDF بعدة سيناريوهات"""
    
    # بيانات اختبار 1
    test_data_1 = {
        'patient_name_ar': 'أحمد محمد علي السعيد',
        'patient_name_en': 'AHMED MOHAMMED ALI ALSAEED',
        'id_number': '1234567890',
        'nationality_ar': 'سعودي',
        'nationality_en': 'Saudi Arabia',
        'employer_ar': 'شركة أرامكو السعودية',
        'employer_en': 'Saudi Aramco Company',
        'doctor_name_ar': 'د. فاطمة أحمد الزهراني',
        'doctor_name_en': 'DR. FATIMA AHMED ALZAHRANI',
        'position_ar': 'مهندس بترول',
        'position_en': 'Petroleum Engineer',
        'admission_date_gregorian': '15-06-2025',
        'admission_date_hijri': '20-12-1446',
        'discharge_date_gregorian': '18-06-2025',
        'discharge_date_hijri': '23-12-1446',
        'issue_date_gregorian': '19-06-2025',
        'hospital_name_ar': 'مستشفى الملك فهد التخصصي',
        'hospital_name_en': 'King Fahd Specialist Hospital',
        'time': '10:30 AM'
    }
    
    # بيانات اختبار 2
    test_data_2 = {
        'patient_name_ar': 'سارة عبدالله محمد القحطاني',
        'patient_name_en': 'SARAH ABDULLAH MOHAMMED ALQAHTANI',
        'id_number': '2987654321',
        'nationality_ar': 'سعودية',
        'nationality_en': 'Saudi Arabia',
        'employer_ar': 'وزارة التعليم',
        'employer_en': 'Ministry of Education',
        'doctor_name_ar': 'د. خالد سعد الغامدي',
        'doctor_name_en': 'DR. KHALID SAAD ALGHAMDI',
        'position_ar': 'معلمة رياضيات',
        'position_en': 'Mathematics Teacher',
        'admission_date_gregorian': '01-07-2025',
        'admission_date_hijri': '06-01-1447',
        'discharge_date_gregorian': '01-07-2025',
        'discharge_date_hijri': '06-01-1447',
        'issue_date_gregorian': '02-07-2025',
        'hospital_name_ar': 'مجمع الرياض الطبي',
        'hospital_name_en': 'Riyadh Medical Complex',
        'time': '2:15 PM'
    }
    
    # بيانات اختبار 3 - إجازة طويلة
    test_data_3 = {
        'patient_name_ar': 'عبدالرحمن يوسف إبراهيم النعيمي',
        'patient_name_en': 'ABDULRAHMAN YOUSSEF IBRAHIM ALNAIMI',
        'id_number': '1122334455',
        'nationality_ar': 'سعودي',
        'nationality_en': 'Saudi Arabia',
        'employer_ar': 'البنك الأهلي السعودي',
        'employer_en': 'National Commercial Bank',
        'doctor_name_ar': 'د. منى حسن الشهري',
        'doctor_name_en': 'DR. MONA HASSAN ALSHAHRI',
        'position_ar': 'مدير فرع',
        'position_en': 'Branch Manager',
        'admission_date_gregorian': '10-07-2025',
        'admission_date_hijri': '15-01-1447',
        'discharge_date_gregorian': '20-07-2025',
        'discharge_date_hijri': '25-01-1447',
        'issue_date_gregorian': '21-07-2025',
        'hospital_name_ar': 'مستشفى الملك عبدالعزيز الجامعي',
        'hospital_name_en': 'King Abdulaziz University Hospital',
        'time': '8:45 AM'
    }
    
    test_cases = [
        ("Test Case 1 - Aramco Employee", test_data_1),
        ("Test Case 2 - Teacher", test_data_2),
        ("Test Case 3 - Bank Manager", test_data_3)
    ]
    
    print("🧪 بدء اختبار توليد ملفات PDF...")
    print("=" * 50)
    
    for case_name, test_data in test_cases:
        try:
            print(f"\n📋 {case_name}")
            print(f"   المريض: {test_data['patient_name_ar']}")
            print(f"   رقم الهوية: {test_data['id_number']}")
            print(f"   المنشأة: {test_data['hospital_name_ar']}")
            
            # توليد ملف PDF
            pdf_path = generate_sick_leave_pdf(test_data, f"test_{test_data['id_number']}")
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024  # KB
                print(f"   ✅ تم إنشاء الملف بنجاح: {os.path.basename(pdf_path)}")
                print(f"   📁 حجم الملف: {file_size:.1f} KB")
            else:
                print(f"   ❌ فشل في إنشاء الملف")
                
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 انتهاء الاختبار")
    
    # عرض قائمة الملفات المولدة
    output_files = [f for f in os.listdir('/home/ubuntu/output') if f.endswith('.pdf')]
    if output_files:
        print(f"\n📂 الملفات المولدة ({len(output_files)} ملف):")
        for file in sorted(output_files):
            print(f"   • {file}")
    else:
        print("\n❌ لم يتم توليد أي ملفات")

def test_edge_cases():
    """اختبار حالات خاصة"""
    print("\n🔍 اختبار الحالات الخاصة...")
    
    # حالة بيانات ناقصة
    incomplete_data = {
        'patient_name_ar': 'مريض تجريبي',
        'patient_name_en': 'TEST PATIENT',
        'id_number': '9999999999',
        'nationality_ar': 'سعودي',
        'nationality_en': 'Saudi Arabia',
        'admission_date_gregorian': '01-01-2025',
        'discharge_date_gregorian': '01-01-2025',
        'issue_date_gregorian': '02-01-2025',
        # باقي البيانات مفقودة
    }
    
    try:
        pdf_path = generate_sick_leave_pdf(incomplete_data, "test_incomplete")
        print("✅ تم التعامل مع البيانات الناقصة بنجاح")
    except Exception as e:
        print(f"❌ خطأ في التعامل مع البيانات الناقصة: {e}")

if __name__ == "__main__":
    test_pdf_generation()
    test_edge_cases()
    
    print("\n🏁 انتهاء جميع الاختبارات")

