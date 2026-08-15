"""
API routes للإجازات المرضية
Medical Leaves API Routes
"""

from flask import Blueprint, request, jsonify
from src.models.medical_leave import MedicalLeave

medical_leaves_bp = Blueprint('medical_leaves', __name__)
medical_leave_model = MedicalLeave()

@medical_leaves_bp.route('/api/medical-leaves', methods=['POST'])
def create_medical_leave():
    """إنشاء إجازة مرضية جديدة"""
    try:
        data = request.get_json()
        
        # التحقق من وجود البيانات المطلوبة
        required_fields = [
            'service_code', 'identity_number', 'patient_name_ar', 'patient_name_en',
            'nationality_ar', 'nationality_en', 'workplace_ar', 'workplace_en',
            'doctor_name_ar', 'doctor_name_en', 'job_title_ar', 'job_title_en',
            'admission_date_gregorian', 'admission_date_hijri', 'discharge_date_gregorian', 
            'discharge_date_hijri', 'report_issue_date', 'facility_name_ar', 
            'facility_name_en', 'report_time', 'duration_days'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # إنشاء الإجازة المرضية
        success = medical_leave_model.create_medical_leave(data)
        
        if success:
            return jsonify({'message': 'تم حفظ البيانات بنجاح'}), 201
        else:
            return jsonify({'error': 'رمز الخدمة موجود مسبقاً أو حدث خطأ في الحفظ'}), 400
            
    except Exception as e:
        return jsonify({'error': f'خطأ في الخادم: {str(e)}'}), 500

@medical_leaves_bp.route('/api/medical-leaves/search', methods=['POST'])
def search_medical_leave():
    """البحث عن إجازة مرضية برمز الخدمة ورقم الهوية"""
    try:
        data = request.get_json()
        
        service_code = data.get('service_code', '').strip()
        identity_number = data.get('identity_number', '').strip()
        
        if not service_code or not identity_number:
            return jsonify({'error': 'رمز الخدمة ورقم الهوية مطلوبان'}), 400
        
        # البحث عن الإجازة المرضية
        medical_leave = medical_leave_model.get_medical_leave_by_service_and_identity(
            service_code, identity_number
        )
        
        if medical_leave:
            return jsonify({
                'found': True,
                'data': medical_leave
            }), 200
        else:
            return jsonify({
                'found': False,
                'message': 'لم يتم العثور على بيانات مطابقة'
            }), 404
            
    except Exception as e:
        return jsonify({'error': f'خطأ في الخادم: {str(e)}'}), 500

@medical_leaves_bp.route('/api/medical-leaves', methods=['GET'])
def get_all_medical_leaves():
    """الحصول على جميع الإجازات المرضية"""
    try:
        medical_leaves = medical_leave_model.get_all_medical_leaves()
        return jsonify({'data': medical_leaves}), 200
    except Exception as e:
        return jsonify({'error': f'خطأ في الخادم: {str(e)}'}), 500

@medical_leaves_bp.route('/api/medical-leaves/<service_code>', methods=['PUT'])
def update_medical_leave(service_code):
    """تحديث إجازة مرضية موجودة"""
    try:
        data = request.get_json()
        
        # التحقق من وجود البيانات المطلوبة
        required_fields = [
            'identity_number', 'patient_name_ar', 'patient_name_en',
            'nationality_ar', 'nationality_en', 'workplace_ar', 'workplace_en',
            'doctor_name_ar', 'doctor_name_en', 'job_title_ar', 'job_title_en',
            'admission_date_gregorian', 'admission_date_hijri', 'discharge_date_gregorian', 
            'discharge_date_hijri', 'report_issue_date', 'facility_name_ar', 
            'facility_name_en', 'report_time', 'duration_days'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # تحديث الإجازة المرضية
        success = medical_leave_model.update_medical_leave(service_code, data)
        
        if success:
            return jsonify({'message': 'تم تحديث البيانات بنجاح'}), 200
        else:
            return jsonify({'error': 'لم يتم العثور على الإجازة المرضية أو حدث خطأ في التحديث'}), 404
            
    except Exception as e:
        return jsonify({'error': f'خطأ في الخادم: {str(e)}'}), 500

@medical_leaves_bp.route('/api/medical-leaves/<service_code>', methods=['DELETE'])
def delete_medical_leave(service_code):
    """حذف إجازة مرضية"""
    try:
        success = medical_leave_model.delete_medical_leave(service_code)
        
        if success:
            return jsonify({'message': 'تم حذف الإجازة المرضية بنجاح'}), 200
        else:
            return jsonify({'error': 'لم يتم العثور على الإجازة المرضية'}), 404
            
    except Exception as e:
        return jsonify({'error': f'خطأ في الخادم: {str(e)}'}), 500
