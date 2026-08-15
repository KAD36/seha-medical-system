#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced PDF Generator for Seha Sick Leave Reports with Arabic Text Support - Final Version
وحدة توليد تقارير الإجازة المرضية بصيغة PDF - النسخة النهائية مع التعديلات المطلوبة
"""

import os
import qrcode
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from config import *
import arabic_reshaper
from bidi.algorithm import get_display

class SickLeavePDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format=(PDF_WIDTH, PDF_HEIGHT))
        self.set_auto_page_break(auto=False)
        
        # تحميل الخطوط
        self.load_fonts()
    
    def load_fonts(self):
        """تحميل الخطوط المطلوبة"""
        try:
            # خطوط عربية
            self.add_font('NotoSansArabic-Bold', '', NOTO_SANS_ARABIC_BOLD)
            self.add_font('NotoSansArabic-Regular', '', NOTO_SANS_ARABIC_REGULAR)
            
            # خطوط إنجليزية - استخدام الخطوط المدمجة إذا لم تعمل الخطوط المخصصة
            try:
                self.add_font('TimesNRMTPro-Bold', '', TIMES_NR_MT_BOLD)
                self.add_font('TimesNRMTPro-Regular', '', TIMES_NR_MT_REGULAR)
                self.times_available = True
            except:
                self.times_available = False
                print("استخدام الخطوط المدمجة للنصوص الإنجليزية")
            
        except Exception as e:
            print(f"خطأ في تحميل الخطوط: {e}")
    
    def process_arabic_text(self, text):
        """معالجة النص العربي لعرضه بشكل صحيح"""
        if not text:
            return ""
        
        try:
            # إعادة تشكيل النص العربي
            reshaped_text = arabic_reshaper.reshape(text)
            # تطبيق خوارزمية BiDi للعرض الصحيح
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            print(f"خطأ في معالجة النص العربي: {e}")
            return text
    
    def add_header_images(self):
        """إضافة الصور والشعارات في الرأس"""
        try:
            # شعار صحة seha (الموقع: الارتفاع من 12 مم إلى 38 مم، العرض من 11 مم إلى 67 مم)
            if os.path.exists(SEHA_LOGO):
                self.image(SEHA_LOGO, x=11, y=12, w=56, h=26)
            
            # الشكل الهندسي (الموقع: الارتفاع من 12 مم إلى 52 مم، العرض من 191 مم إلى 285 مم)
            if os.path.exists(GEOMETRIC_SHAPE):
                self.image(GEOMETRIC_SHAPE, x=191, y=12, w=94, h=40)
            
            # صورة كلمة المملكة العربية السعودية (الموقع: الارتفاع من 13 مم إلى 58 مم، العرض من 100 مم إلى 194 مم)
            if os.path.exists(KINGDOM_TEXT):
                self.image(KINGDOM_TEXT, x=100, y=13, w=94, h=45)
                
        except Exception as e:
            print(f"خطأ في إضافة صور الرأس: {e}")
    
    def add_titles(self):
        """إضافة العناوين الرئيسية"""
        # تقرير إجازة مرضية (الموقع: الارتفاع من 57 مم إلى 67 مم، العرض من 116 مم إلى 184 مم)
        self.set_font('NotoSansArabic-Bold', size=22)
        self.set_text_color(48, 109, 181)  # #306db5
        self.set_xy(116, 57)
        arabic_title = self.process_arabic_text('تقرير إجازة مرضية')
        self.cell(68, 10, arabic_title, align='C')
        
        # Sick Leave Report (الموقع: الارتفاع من 69 مم إلى 76 مم، العرض من 123 مم إلى 175 مم)
        if self.times_available:
            self.set_font('TimesNRMTPro-Bold', size=18)
        else:
            self.set_font('Arial', 'B', size=18)
        self.set_text_color(44, 62, 119)  # #2c3e77
        self.set_xy(123, 69)
        self.cell(52, 7, 'Sick Leave Report', align='C')
    
    def generate_leave_id(self, id_number, admission_date, discharge_date):
        """توليد رمز الإجازة"""
        # PSL + رقم مكون من رقم الهوية وتاريخ الدخول والخروج (11 رقم)
        id_part = id_number[-4:] if len(id_number) >= 4 else id_number
        
        # استخراج الأرقام من التواريخ
        admission_nums = ''.join(filter(str.isdigit, admission_date))[-3:]
        discharge_nums = ''.join(filter(str.isdigit, discharge_date))[-4:]
        
        # تكوين الرقم (11 رقم)
        leave_number = (id_part + admission_nums + discharge_nums).ljust(11, '0')[:11]
        
        return f"PSL{leave_number}"
    
    def calculate_duration(self, admission_date_hijri, discharge_date_hijri, admission_date_gregorian, discharge_date_gregorian):
        """حساب مدة الإجازة"""
        try:
            # تحويل التواريخ الميلادية لحساب المدة
            admission_parts = admission_date_gregorian.split('-')
            discharge_parts = discharge_date_gregorian.split('-')
            
            if len(admission_parts) == 3 and len(discharge_parts) == 3:
                admission_dt = datetime(int(admission_parts[2]), int(admission_parts[1]), int(admission_parts[0]))
                discharge_dt = datetime(int(discharge_parts[2]), int(discharge_parts[1]), int(discharge_parts[0]))
                
                duration_days = (discharge_dt - admission_dt).days + 1
                
                # تكوين النص العربي
                duration_ar = f"{duration_days} يوم ({admission_date_hijri} إلى {discharge_date_hijri})"
                
                # تكوين النص الإنجليزي
                day_word = "day" if duration_days == 1 else "days"
                duration_en = f"{duration_days} {day_word} ({admission_date_gregorian} to {discharge_date_gregorian})"
                
                return duration_ar, duration_en
            else:
                duration_ar = f"1 يوم ({admission_date_hijri} إلى {discharge_date_hijri})"
                duration_en = f"1 day ({admission_date_gregorian} to {discharge_date_gregorian})"
                return duration_ar, duration_en
                
        except Exception as e:
            print(f"خطأ في حساب المدة: {e}")
            duration_ar = f"1 يوم ({admission_date_hijri} إلى {discharge_date_hijri})"
            duration_en = f"1 day ({admission_date_gregorian} to {discharge_date_gregorian})"
            return duration_ar, duration_en
    
    def add_table(self, data):
        """إضافة الجدول الرئيسي"""
        # موقع الجدول
        table_x = 12.5
        table_y = 85
        
        # أبعاد الأعمدة (بعد التبديل: العمود الرابع، الثالث، الثاني، الأول)
        col_widths = [58, 83, 83, 48]
        
        # ارتفاعات الصفوف
        row_heights = [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]
        
        # ألوان خلفية الصفوف
        row_bg_colors = {
            1: (44, 62, 119),    # #2c3e77 - صف مدة الإجازة
            3: (247, 247, 247),  # #f7f7f7
            5: (247, 247, 247),  # #f7f7f7
            7: (247, 247, 247),  # #f7f7f7
            9: (247, 247, 247),  # #f7f7f7
        }
        
        # توليد البيانات
        leave_id = self.generate_leave_id(
            data.get('id_number', '1234567890'),
            data.get('admission_date_gregorian', '01-01-2025'),
            data.get('discharge_date_gregorian', '01-01-2025')
        )
        
        duration_ar, duration_en = self.calculate_duration(
            data.get('admission_date_hijri', '01-01-1446'),
            data.get('discharge_date_hijri', '01-01-1446'),
            data.get('admission_date_gregorian', '01-01-2025'),
            data.get('discharge_date_gregorian', '01-01-2025')
        )
        
        # معالجة النصوص العربية
        processed_data = {}
        for key, value in data.items():
            if key.endswith('_ar') and value:
                processed_data[key] = self.process_arabic_text(value)
            else:
                processed_data[key] = value
        
        # معالجة النصوص الثابتة العربية
        duration_ar_processed = self.process_arabic_text(duration_ar)
        
        # محتوى الجدول (بعد التبديل)
        table_data = [
            # [العمود الرابع (إنجليزي), العمود الثالث (إنجليزي/بيانات), العمود الثاني (عربي/بيانات), العمود الأول (عربي)]
            ['Leave ID', leave_id, '', self.process_arabic_text('رمز الإجازة')],
            ['Leave Duration', duration_en, duration_ar_processed, self.process_arabic_text('مدة الإجازة')],
            ['Admission Date', processed_data.get('admission_date_gregorian', ''), processed_data.get('admission_date_hijri', ''), self.process_arabic_text('تاريخ الدخول')],
            ['Discharge Date', processed_data.get('discharge_date_gregorian', ''), processed_data.get('discharge_date_hijri', ''), self.process_arabic_text('تاريخ الخروج')],
            ['Issue Date', processed_data.get('issue_date_gregorian', ''), '', self.process_arabic_text('تاريخ إصدار التقرير')],
            ['Name', processed_data.get('patient_name_en', ''), processed_data.get('patient_name_ar', ''), self.process_arabic_text('الاسم')],
            ['National ID / Iqama', processed_data.get('id_number', ''), '', self.process_arabic_text('رقم الهوية / الإقامة')],
            ['Nationality', processed_data.get('nationality_en', ''), processed_data.get('nationality_ar', ''), self.process_arabic_text('الجنسية')],
            ['Employer', processed_data.get('employer_en', ''), processed_data.get('employer_ar', ''), self.process_arabic_text('جهة العمل')],
            ["Practitioner Name", processed_data.get("doctor_name_en", ""), processed_data.get("doctor_name_ar", ""), self.process_arabic_text("اسم الممارس")],
            ['Position', processed_data.get('position_en', ''), processed_data.get('position_ar', ''), self.process_arabic_text('المسمى الوظيفي')],
        ]
        
        # رسم الجدول
        current_y = table_y
        
        for row_idx, row_data in enumerate(table_data):
            current_x = table_x
            row_height = row_heights[row_idx]
            
            # تعيين لون الخلفية للصف
            if row_idx in row_bg_colors:
                self.set_fill_color(*row_bg_colors[row_idx])
                fill = True
            else:
                fill = False
            
            # رسم الخلايا
            for col_idx, cell_text in enumerate(row_data):
                col_width = col_widths[col_idx]
                
                # تخطي الخلايا المدمجة
                if self.is_merged_cell(row_idx, col_idx):
                    current_x += col_width
                    continue
                
                # تحديد عرض الخلية للخلايا المدمجة
                actual_width = col_width
                if self.is_merge_start(row_idx, col_idx):
                    actual_width = col_widths[col_idx] + col_widths[col_idx + 1]
                
                # رسم حدود الخلية
                self.set_draw_color(217, 217, 217)  # #D9D9D9
                self.set_line_width(0.5)
                self.rect(current_x, current_y, actual_width, row_height, 'D' if not fill else 'DF')
                
                # تعيين الخط واللون
                self.set_cell_font_and_color(row_idx, col_idx, cell_text)
                
                # كتابة النص
                if cell_text:  # فقط إذا كان هناك نص
                    self.set_xy(current_x, current_y)
                    align = self.get_cell_alignment(row_idx, col_idx)
                    self.cell(actual_width, row_height, cell_text, align=align)
                current_x += col_width
            
            current_y += row_height
        
        # إضافة الخط العمودي
        self.set_draw_color(217, 217, 217)  # #D9D9D9
        self.set_line_width(0.5)
        self.line(152, 254, 152, 335) # x1, y1, x2, y2
    
    def is_merged_cell(self, row_idx, col_idx):
        """تحديد ما إذا كانت الخلية مدمجة"""
        # الخلايا المدمجة: الصف الأول (0,4,6) العمود الثاني والثالث
        if row_idx in [0, 4, 6] and col_idx == 2:
            return True
        return False
    
    def is_merge_start(self, row_idx, col_idx):
        """تحديد ما إذا كانت الخلية بداية دمج"""
        if row_idx in [0, 4, 6] and col_idx == 1:
            return True
        return False
    
    def set_cell_font_and_color(self, row_idx, col_idx, text):
        """تعيين الخط واللون للخلية"""
        # الألوان
        blue_color = (54, 111, 181)    # #366fb5
        dark_blue = (44, 62, 119)      # #2c3e77
        white_color = (255, 255, 255)  # #ffffff
        
        if row_idx == 1:  # صف مدة الإجازة
            if col_idx in [0, 3]:  # العمود الأول والرابع
                if col_idx == 0:
                    if self.times_available:
                        self.set_font('TimesNRMTPro-Bold', size=13)
                    else:
                        self.set_font('Arial', 'B', size=13)
                else:
                    self.set_font('NotoSansArabic-Bold', size=13)
                self.set_text_color(*white_color)
            else:  # العمود الثاني والثالث
                if col_idx == 1:
                    if self.times_available:
                        self.set_font('TimesNRMTPro-Regular', size=13)
                    else:
                        self.set_font('Arial', '', size=13)
                else:
                    self.set_font('NotoSansArabic-Regular', size=13)
                self.set_text_color(*white_color)
        elif col_idx == 0:  # العمود الرابع (إنجليزي)
            if self.times_available:
                self.set_font('TimesNRMTPro-Bold', size=13)
            else:
                self.set_font('Arial', 'B', size=13)
            self.set_text_color(*blue_color)
        elif col_idx == 1:  # العمود الثالث (إنجليزي/بيانات)
            # تحديد حجم الخط - 11pt للصف السادس (الاسم)، 11pt للصفوف الأخرى
            if row_idx == 5:  # الصف السادس (الاسم)
                font_size = 11
            else:
                font_size = 11 if row_idx in [7, 9] else 13
            
            if self.times_available:
                self.set_font('TimesNRMTPro-Regular', size=font_size)
            else:
                self.set_font('Arial', '', size=font_size)
            self.set_text_color(*dark_blue)
        elif col_idx == 2:  # العمود الثاني (عربي/بيانات)
            self.set_font('NotoSansArabic-Regular', size=13)
            self.set_text_color(*dark_blue)
        elif col_idx == 3:  # العمود الأول (عربي)
            self.set_font('NotoSansArabic-Bold', size=13)
            self.set_text_color(*blue_color)
    
    def get_cell_alignment(self, row_idx, col_idx):
        """تحديد محاذاة النص في الخلية"""
        # الصفوف المدمجة والخاصة
        if row_idx in [0, 4, 6] and col_idx == 1:  # الخلايا المدمجة
            return 'C'
        elif col_idx == 1:  # العمود الثالث
            # العمود الثالث الصف الثالث والرابع - المحاذاة وسط
            if row_idx in [2, 3]:  # الصف الثالث والرابع
                return 'C'
            else:
                return 'C'
        else:
            return 'C'
    
    def add_footer_elements(self, data):
        """إضافة عناصر التذييل"""
        try:
            # إنشاء الباركود
            qr_data = f"{data.get('id_number', '')} - {self.generate_leave_id(data.get('id_number', ''), data.get('admission_date_gregorian', ''), data.get('discharge_date_gregorian', ''))} - {data.get('issue_date_gregorian', '')}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(QR_URL)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_path = f"{OUTPUT_DIR}/temp_qr.png"
            qr_img.save(qr_path)
            
            # إضافة الباركود
            self.image(qr_path, x=60, y=265, w=42, h=40)
            
            # حذف الملف المؤقت
            if os.path.exists(qr_path):
                os.remove(qr_path)
            
            # شعار المنشأة
            custom_logo = data.get('custom_logo')
            if custom_logo and os.path.exists(custom_logo):
                self.image(custom_logo, x=203, y=266, w=43, h=42)
            elif os.path.exists(HOSPITAL_LOGO):
                self.image(HOSPITAL_LOGO, x=203, y=266, w=43, h=42)
            
            # اسم المنشأة
            hospital_name_ar = data.get('hospital_name_ar', 'مجمع عائلتي الطبي')
            hospital_name_en = data.get('hospital_name_en', 'My Family Medical Center')
            
            # النص العربي
            self.set_font('NotoSansArabic-Bold', size=12)
            self.set_text_color(0, 0, 0)
            self.set_xy(188, 309)
            processed_hospital_name = self.process_arabic_text(hospital_name_ar)
            self.cell(67, 10, processed_hospital_name, align='C')
            
            # النص الإنجليزي
            if self.times_available:
                self.set_font('TimesNRMTPro-Bold', size=12)
            else:
                self.set_font('Arial', 'B', size=12)
            self.set_xy(188, 320)
            self.cell(67, 10, hospital_name_en, align='C')
            
            # النصوص التحققية
            self.set_font('NotoSansArabic-Bold', size=11)
            self.set_text_color(0, 0, 0)
            self.set_xy(24, 308)
            verification_text = self.process_arabic_text('للتحقق من بيانات التقرير يرجى التأكد من زيارة موقع منصة صحة الرسمي')
            self.cell(112, 10, verification_text, align='C')
            
            if self.times_available:
                self.set_font('TimesNRMTPro-Bold', size=11)
            else:
                self.set_font('Arial', 'B', size=11)
            self.set_xy(24, 318)
            self.cell(112, 10, 'To Check the report please visit seha\'s official website', align='C')
            
            # الرابط
            if self.times_available:
                self.set_font('TimesNRMTPro-Bold', size=11)
            else:
                self.set_font('Arial', 'B', size=11)
            self.set_text_color(0, 0, 255)  # #0000ff
            self.set_xy(48, 330)
            self.cell(60, 7, QR_URL, align='C', link=QR_URL)
            
            # رسم خط تحت الرابط بسماكة أقل
            self.set_draw_color(0, 0, 255)
            self.set_line_width(0.2)  # تقليل سماكة الخط
            self.line(48, 337, 108, 337)
            
            # شعار المركز الوطني للمعلومات الصحية
            if os.path.exists(HEALTH_INFO_CENTER_LOGO):
                self.image(HEALTH_INFO_CENTER_LOGO, x=231, y=336, w=54, h=26)
            
            # الوقت والتاريخ
            current_time = data.get('time', '6:23 AM')
            current_date = datetime.now().strftime('%A, %d %B %Y')
            
            if self.times_available:
                self.set_font('TimesNRMTPro-Bold', size=12)
            else:
                self.set_font('Arial', 'B', size=12)
            self.set_text_color(0, 0, 0)
            self.set_xy(11, 339)
            self.cell(20, 6, current_time, align='L')
            
            self.set_xy(11, 347)
            self.cell(47, 6, current_date, align='L')
            
        except Exception as e:
            print(f"خطأ في إضافة عناصر التذييل: {e}")

def generate_sick_leave_pdf(data, user_id):
    """توليد تقرير الإجازة المرضية"""
    try:
        # إنشاء مجلد الإخراج
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # إنشاء ملف PDF
        pdf = SickLeavePDF()
        pdf.add_page()
        
        # إضافة العناصر
        pdf.add_header_images()
        pdf.add_titles()
        pdf.add_table(data)
        pdf.add_footer_elements(data)
        
        # حفظ الملف
        id_number = data.get('id_number', 'UNKNOWN')
        issue_date = data.get('issue_date_gregorian', datetime.now().strftime('%d-%m-%Y'))
        filename = f"Sick Leave{id_number}_{issue_date.replace('-', '')}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        pdf.output(filepath)
        
        return filepath
        
    except Exception as e:
        print(f"خطأ في توليد PDF: {e}")
        raise e

if __name__ == "__main__":
    # اختبار سريع
    test_data = {
        'patient_name_ar': 'أحمد محمد السعيد',
        'patient_name_en': 'AHMED Mohammed Alsaeed',
        'id_number': '1122923749',
        'nationality_ar': 'سعودي',
        'nationality_en': 'Saudi Arabia',
        'employer_ar': 'طالب جامعي',
        'employer_en': 'University Student',
        'doctor_name_ar': 'نبيل حنا نصر حنا',
        'doctor_name_en': 'NABIL HANNA NASR HANNA',
        'position_ar': 'طبيب عام',
        'position_en': 'General',
        'admission_date_gregorian': '12-05-2025',
        'admission_date_hijri': '14-11-1446',
        'discharge_date_gregorian': '12-05-2025',
        'discharge_date_hijri': '14-11-1446',
        'issue_date_gregorian': '05-07-2025',
        'hospital_name_ar': 'مجمع عائلتي الطبي',
        'hospital_name_en': 'My Family Medical Center',
        'time': '6:23 AM'
    }
    
    pdf_path = generate_sick_leave_pdf(test_data, 'test')
    print(f"تم إنشاء ملف PDF: {pdf_path}")

