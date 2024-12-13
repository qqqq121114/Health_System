from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import db, HealthRecord, FollowUp
from . import patient_bp

# 定义记录类型映射
RECORD_TYPES = {
    'MEDICAL_HISTORY': '病史记录',
    'PHYSICAL_EXAM': '体检报告',
    'DAILY_MONITOR': '日常监测'
}

@patient_bp.route('/health_records')
@login_required
def health_records():
    """健康记录页面"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    # 获取筛选参数
    record_type = request.args.get('record_type')
    time_range = request.args.get('time_range')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 构建基础查询
    query = HealthRecord.query.filter_by(patient_id=current_user.id)
    
    # 应用记录类型筛选
    if record_type:
        query = query.filter_by(record_type=record_type)
    
    # 应用时间范围筛选
    if time_range:
        today = datetime.now().date()
        if time_range == 'today':
            # 使用SQLite的date函数
            query = query.filter(db.text("date(record_date) = date('now', 'localtime')"))
        elif time_range == 'week':
            # 最近一周
            query = query.filter(db.text("date(record_date) >= date('now', 'localtime', '-7 days')"))
        elif time_range == 'month':
            # 最近一个月
            query = query.filter(db.text("date(record_date) >= date('now', 'localtime', '-30 days')"))
        elif time_range == 'year':
            # 最近一年
            query = query.filter(db.text("date(record_date) >= date('now', 'localtime', '-365 days')"))
    # 应用自定义日期范围筛选
    elif start_date or end_date:
        if start_date:
            query = query.filter(db.text("date(record_date) >= date(:start_date)")).params(start_date=start_date)
        if end_date:
            query = query.filter(db.text("date(record_date) <= date(:end_date)")).params(end_date=end_date)
    
    # 获取结果并按日期降序排序
    records = query.order_by(HealthRecord.record_date.desc()).all()
    
    # 转换记录类型为中文
    for record in records:
        record.record_type = RECORD_TYPES.get(record.record_type, record.record_type)
    
    return render_template('patient/health_records.html', records=records)

@patient_bp.route('/add_health_record', methods=['POST'])
@login_required
def add_health_record():
    """添加健康记录"""
    if current_user.role != 'PATIENT':
        error_msg = '无权进行此操作'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 403
        flash(error_msg, 'danger')
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        record_type = request.form.get('record_type')
        if not record_type:
            raise ValueError('记录类型不能为空')
        
        record_date_str = request.form.get('record_date')
        if not record_date_str:
            raise ValueError('记录日期不能为空')
        
        # 将日期字符串转换为datetime对象，保持格式一致
        record_date = datetime.strptime(record_date_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        
        # 创建新记录
        new_record = HealthRecord(
            patient_id=current_user.id,
            doctor_id=None,  # 初始设置为None，等待医生审核
            record_type=record_type,
            record_date=record_date,
            description=request.form.get('description'),
            symptoms=request.form.get('symptoms'),
            height=request.form.get('height', type=float),
            weight=request.form.get('weight', type=float),
            blood_pressure=f"{request.form.get('blood_pressure_sys', '')}/{request.form.get('blood_pressure_dia', '')}",
            heart_rate=request.form.get('heart_rate', type=int),
            blood_sugar=request.form.get('blood_sugar', type=float),
            blood_routine=request.form.get('blood_routine'),
            urine_routine=request.form.get('urine_routine'),
            liver_function=request.form.get('liver_function'),
            kidney_function=request.form.get('kidney_function'),
            temperature=request.form.get('body_temperature', type=float)
        )
        
        db.session.add(new_record)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '健康记录添加成功！'})
        
        flash('健康记录添加成功！', 'success')
        return redirect(url_for('patient.health_records'))
        
    except ValueError as e:
        db.session.rollback()
        error_msg = str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(url_for('patient.health_records'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = '添加记录失败，请重试'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'danger')
        return redirect(url_for('patient.health_records'))

@patient_bp.route('/view_record/<int:record_id>')
@login_required
def view_record(record_id):
    """查看健康记录详情"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    record = HealthRecord.query.get_or_404(record_id)
    if record.patient_id != current_user.id:
        flash('无权查看此记录', 'danger')
        return redirect(url_for('patient.health_records'))
    
    return render_template('patient/view_record.html', record=record)

@patient_bp.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    """删除健康记录"""
    if current_user.role != 'PATIENT':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '无权进行此操作'}), 403
        flash('无权进行此操作', 'danger')
        return redirect(url_for('index'))
    
    record = HealthRecord.query.get_or_404(record_id)
    if record.patient_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '无权删除此记录'}), 403
        flash('无权删除此记录', 'danger')
        return redirect(url_for('patient.health_records'))
    
    try:
        db.session.delete(record)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '记录已删除'})
        
        flash('记录已删除', 'success')
        return redirect(url_for('patient.health_records'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = '删除失败，请重试'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'danger')
        return redirect(url_for('patient.health_records')) 