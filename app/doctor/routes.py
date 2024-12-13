from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, User, HealthRecord, FollowUp
from . import doctor_bp

@doctor_bp.route('/doctor/home')
@login_required
def home():
    """医生工作台首页"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取统计数据
    today = datetime.now().date()
    pending_patients = 0  # 待处理患者数
    today_records = HealthRecord.query.filter(
        db.func.date(HealthRecord.record_date) == today
    ).count()  # 今日新增记录数
    abnormal_records = 0  # 异常指标数
    
    # 获取最近活动
    recent_activities = []
    
    return render_template('doctor/doctor_home.html',
                         pending_patients=pending_patients,
                         today_records=today_records,
                         abnormal_records=abnormal_records,
                         recent_activities=recent_activities)

@doctor_bp.route('/doctor/patient_list')
@login_required
def patient_list():
    """患者列表页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取患者列表并分页
    pagination = User.query.filter_by(role='PATIENT').paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('doctor/patient_list.html',
                         patients=pagination.items,
                         page=page,
                         pages=pagination.pages)

@doctor_bp.route('/doctor/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    """添加就诊记录"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            patient_id = request.form.get('patient_id')
            record_type = request.form.get('record_type')
            record_date = request.form.get('record_date')
            
            # 创建新记录
            new_record = HealthRecord(
                patient_id=patient_id,
                doctor_id=current_user.id,
                record_type=record_type,
                record_date=datetime.strptime(record_date, '%Y-%m-%d'),
                symptoms=request.form.get('symptoms'),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                height=request.form.get('height', type=float),
                weight=request.form.get('weight', type=float),
                blood_pressure=f"{request.form.get('blood_pressure_sys', '')}/{request.form.get('blood_pressure_dia', '')}",
                heart_rate=request.form.get('heart_rate', type=int),
                blood_sugar=request.form.get('blood_sugar', type=float)
            )
            
            db.session.add(new_record)
            db.session.commit()
            flash('就诊记录添加成功！', 'success')
            return redirect(url_for('doctor.patient_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('添加记录失败，请重试', 'danger')
            print(f"Error adding record: {str(e)}")
            return redirect(url_for('doctor.add_record'))
    
    return render_template('doctor/add_record.html')

@doctor_bp.route('/view_patient/<int:patient_id>')
@login_required
def view_patient(patient_id):
    """查看患者详情页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
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
        return redirect(url_for('main.index'))
    
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