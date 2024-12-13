from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
from app.models import db, User, HealthRecord, FollowUp
from . import doctor_bp

@doctor_bp.route('/home')
@login_required
def home():
    """医生工作台首页"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    # 获取今日就诊数
    today_date = datetime.now().date()
    today_visits = HealthRecord.query.filter(
        HealthRecord.doctor_id == current_user.id,
        func.date(HealthRecord.record_date) == today_date
    ).count()
    
    # 获取待复诊数量
    follow_up_count = FollowUp.query.filter_by(
        doctor_id=current_user.id,
        status='pending'
    ).count()
    
    # 获取本月新增患者数
    current_month = datetime.now()
    new_patients_month = User.query.filter(
        User.role == 'PATIENT',
        func.extract('month', User.created_at) == current_month.month,
        func.extract('year', User.created_at) == current_month.year
    ).count()
    
    # 获取总患者数和我的患者数
    total_patients = User.query.filter_by(role='PATIENT').count()
    my_patients = User.query.filter_by(role='PATIENT')\
        .join(HealthRecord, User.id == HealthRecord.patient_id)\
        .filter(HealthRecord.doctor_id == current_user.id)\
        .distinct().count()
    
    # 获取最近就诊记录（包含患者信息）
    recent_records = HealthRecord.query\
        .join(User, HealthRecord.patient_id == User.id)\
        .filter(HealthRecord.doctor_id == current_user.id)\
        .order_by(HealthRecord.record_date.desc())\
        .limit(10)\
        .all()
    
    return render_template('doctor/home.html',
                         today_visits=today_visits,
                         follow_up_count=follow_up_count,
                         new_patients_month=new_patients_month,
                         total_patients=total_patients,
                         my_patients=my_patients,
                         recent_records=recent_records)

@doctor_bp.route('/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    """医生添加记录页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 处理添加记录的逻辑
        pass
    
    return render_template('doctor/add_record.html')

@doctor_bp.route('/view_patient/<int:patient_id>')
@login_required
def view_patient(patient_id):
    """查看患者详情页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    patient = User.query.get_or_404(patient_id)
    if patient.role != 'PATIENT':
        flash('无效的患者ID', 'danger')
        return redirect(url_for('doctor.home'))
    
    # 获取患者的健康记录
    records = HealthRecord.query.filter_by(patient_id=patient_id)\
        .order_by(HealthRecord.record_date.desc()).all()
    
    # 获取患者的复诊记录
    follow_ups = FollowUp.query.filter_by(patient_id=patient_id)\
        .order_by(FollowUp.follow_up_date.desc()).all()
    
    return render_template('doctor/view_patient.html',
                         patient=patient,
                         records=records,
                         follow_ups=follow_ups)

@doctor_bp.route('/edit_record/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    """编辑健康记录"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    record = HealthRecord.query.get_or_404(record_id)
    
    # 检查是否是该医生的记录
    if record.doctor_id != current_user.id:
        flash('无权编辑此记录', 'danger')
        return redirect(url_for('doctor.home'))
    
    if request.method == 'POST':
        try:
            # 更新记录
            record.record_type = request.form.get('record_type')
            record.record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d')
            record.description = request.form.get('description')
            record.symptoms = request.form.get('symptoms')
            record.diagnosis = request.form.get('diagnosis')
            record.treatment = request.form.get('treatment')
            record.medications = request.form.get('medications')
            record.height = request.form.get('height', type=float)
            record.weight = request.form.get('weight', type=float)
            record.blood_pressure = f"{request.form.get('blood_pressure_sys', '')}/{request.form.get('blood_pressure_dia', '')}"
            record.heart_rate = request.form.get('heart_rate', type=int)
            record.blood_sugar = request.form.get('blood_sugar', type=float)
            record.blood_fat = request.form.get('blood_fat')
            record.blood_routine = request.form.get('blood_routine')
            record.urine_routine = request.form.get('urine_routine')
            record.liver_function = request.form.get('liver_function')
            record.kidney_function = request.form.get('kidney_function')
            record.temperature = request.form.get('temperature', type=float)
            record.pulse = request.form.get('pulse', type=int)
            record.respiratory_rate = request.form.get('respiratory_rate', type=int)
            record.oxygen_saturation = request.form.get('oxygen_saturation', type=float)
            
            db.session.commit()
            flash('记录更新成功！', 'success')
            return redirect(url_for('doctor.view_patient', patient_id=record.patient_id))
            
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请重试', 'danger')
            print(f"Update error: {str(e)}")
    
    return render_template('doctor/edit_record.html', record=record)

@doctor_bp.route('/check_patient/<username>')
@login_required
def check_patient(username):
    """检查患者信息的API"""
    if current_user.role != 'DOCTOR':
        return jsonify({
            'success': False,
            'message': '无权进行此操作'
        }), 403
    
    patient = User.query.filter_by(username=username, role='PATIENT').first()
    if not patient:
        return jsonify({
            'success': False,
            'message': '未找到该患者'
        }), 404
    
    return jsonify({
        'success': True,
        'patient': {
            'id': patient.id,
            'name': patient.name,
            'gender': patient.gender,
            'age': patient.get_age(),
            'phone': patient.phone
        }
    }) 