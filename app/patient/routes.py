from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import db, HealthRecord, FollowUp
from . import patient_bp
import csv
from io import StringIO

# 定义记录类型映射
RECORD_TYPES = {
    'MEDICAL_HISTORY': '病史记录',
    'PHYSICAL_EXAM': '体检报告',
    'DAILY_MONITOR': '日常监测'
}

@patient_bp.route('/patient/health_records')
@login_required
def health_records():
    """健康记录页面"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    records = HealthRecord.query.filter_by(patient_id=current_user.id).order_by(HealthRecord.record_date.desc()).all()
    return render_template('patient/health_records.html', records=records)

@patient_bp.route('/patient/add_health_record', methods=['POST'])
@login_required
def add_health_record():
    """添加健康记录"""
    if current_user.role != 'PATIENT':
        flash('无权进行此操作', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # 获取表单数据
        record_type = request.form.get('record_type')
        record_date = request.form.get('record_date')
        
        # 创建新记录
        new_record = HealthRecord(
            patient_id=current_user.id,
            record_type=record_type,
            record_date=datetime.strptime(record_date, '%Y-%m-%d'),
            symptoms=request.form.get('symptoms'),
            height=request.form.get('height', type=float),
            weight=request.form.get('weight', type=float),
            blood_pressure=f"{request.form.get('blood_pressure_sys', '')}/{request.form.get('blood_pressure_dia', '')}",
            heart_rate=request.form.get('heart_rate', type=int),
            blood_sugar=request.form.get('blood_sugar', type=float)
        )
        
        db.session.add(new_record)
        db.session.commit()
        flash('健康记录添加成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('添加记录失败，请重试', 'danger')
        print(f"Error adding record: {str(e)}")
    
    return redirect(url_for('patient.health_records'))

@patient_bp.route('/patient/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    """删除健康记录"""
    if current_user.role != 'PATIENT':
        return jsonify({'success': False, 'message': '无权进行此操作'}), 403
    
    record = HealthRecord.query.get_or_404(record_id)
    if record.patient_id != current_user.id:
        return jsonify({'success': False, 'message': '无权删除此记录'}), 403
    
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting record: {str(e)}")
        return jsonify({'success': False, 'message': '删除失败，请重试'}), 500

@patient_bp.route('/patient/export_health_records')
@login_required
def export_health_records():
    """导出健康记录为CSV文件"""
    if current_user.role != 'PATIENT':
        flash('无权进行此操作', 'danger')
        return redirect(url_for('main.index'))
        
    # 获取当前用户的所有健康记录
    records = HealthRecord.query.filter_by(patient_id=current_user.id).order_by(HealthRecord.record_date.desc()).all()
    
    # 创建CSV文件
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(['记录日期', '记录类型', '血压', '心率', '血糖', '体重', '身高', '描述'])
    
    # 写入数据
    for record in records:
        writer.writerow([
            record.record_date.strftime('%Y-%m-%d'),
            record.record_type,
            record.blood_pressure,
            record.heart_rate,
            record.blood_sugar,
            record.weight,
            record.height,
            record.description
        ])
    
    # 设置文件指针到开始位置
    output.seek(0)
    
    # 生成文件名
    filename = f'health_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # 返回CSV文件
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    ) 

@patient_bp.route('/patient/view_record/<int:record_id>')
@login_required
def view_record(record_id):
    """查看健康记录详情"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    record = HealthRecord.query.get_or_404(record_id)
    if record.patient_id != current_user.id:
        flash('无权查看此记录', 'danger')
        return redirect(url_for('patient.health_records'))
    
    return render_template('patient/view_record.html', record=record)