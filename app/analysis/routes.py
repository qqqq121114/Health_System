from flask import render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import HealthRecord, db
from . import analysis_bp

@analysis_bp.route('/health-trends')
@login_required
def health_trends():
    """健康趋势分析"""
    if current_user.role == 'DOCTOR':
        return jsonify({'error': '无权访问'}), 403
    
    # 获取最近90天的记录
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    records = HealthRecord.query.filter(
        HealthRecord.patient_id == current_user.id,
        HealthRecord.record_date.between(start_date, end_date)
    ).order_by(HealthRecord.record_date.asc()).all()
    
    # 提取数据
    dates = [record.record_date.strftime('%Y-%m-%d') for record in records]
    blood_pressure = [record.blood_pressure for record in records]
    blood_sugar = [record.blood_sugar for record in records]
    heart_rate = [record.heart_rate for record in records]
    weight = [record.weight for record in records]
    
    return render_template('analysis/health_trends.html',
                         dates=dates,
                         blood_pressure=blood_pressure,
                         blood_sugar=blood_sugar,
                         heart_rate=heart_rate,
                         weight=weight)

@analysis_bp.route('/risk-assessment')
@login_required
def risk_assessment():
    """健康风险评估"""
    if current_user.role == 'DOCTOR':
        return jsonify({'error': '无权访问'}), 403
    
    # 获取最新记录
    latest_record = HealthRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(HealthRecord.record_date.desc()).first()
    
    if not latest_record:
        return render_template('analysis/risk_assessment.html', risks=[])
    
    # 评估健康风险
    risks = []
    
    # 血压风险评估
    if latest_record.blood_pressure:
        try:
            sys, dia = map(int, latest_record.blood_pressure.split('/'))
            if sys >= 140 or dia >= 90:
                risks.append({
                    'type': '血压',
                    'level': '高',
                    'description': '您的血压偏高，建议定期监测并咨询医生。'
                })
            elif sys <= 90 or dia <= 60:
                risks.append({
                    'type': '血压',
                    'level': '低',
                    'description': '您的血压偏低，建议适当补充营养并咨询医生。'
                })
        except:
            pass
    
    # 血糖风险评估
    if latest_record.blood_sugar:
        if latest_record.blood_sugar > 7.0:
            risks.append({
                'type': '血糖',
                'level': '高',
                'description': '您的血糖水平偏高，建议控制饮食并定期检查。'
            })
        elif latest_record.blood_sugar < 3.9:
            risks.append({
                'type': '血糖',
                'level': '低',
                'description': '您的血糖水平偏低，建议及时补充糖分并咨询医生。'
            })
    
    # 心率风险评估
    if latest_record.heart_rate:
        if latest_record.heart_rate > 100:
            risks.append({
                'type': '心率',
                'level': '高',
                'description': '您的心率偏快，建议注意休息并避免剧烈运动。'
            })
        elif latest_record.heart_rate < 60:
            risks.append({
                'type': '心率',
                'level': '低',
                'description': '您的心率偏慢，建议咨询医生并保持适度运动。'
            })
    
    # 体重风险评估
    if latest_record.height and latest_record.weight:
        # 计算BMI
        height_m = latest_record.height / 100
        bmi = latest_record.weight / (height_m * height_m)
        if bmi >= 28:
            risks.append({
                'type': '体重',
                'level': '高',
                'description': '您的BMI指数偏高，属于肥胖范围，建议控制饮食并加强运动。'
            })
        elif bmi < 18.5:
            risks.append({
                'type': '体重',
                'level': '低',
                'description': '您的BMI指数偏低，属于偏瘦范围，建议适当增加营养摄入。'
            })
    
    return render_template('analysis/risk_assessment.html', risks=risks)

@analysis_bp.route('/health-stats')
@login_required
def health_stats():
    """健康数据统计"""
    if current_user.role == 'DOCTOR':
        return jsonify({'error': '无权访问'}), 403
    
    # 获取各项指标的统计数据
    stats = {
        'blood_pressure': {},
        'blood_sugar': {},
        'heart_rate': {},
        'weight': {}
    }
    
    # 计算血压的平均值、最高值和最低值
    blood_pressure_records = HealthRecord.query.filter(
        HealthRecord.patient_id == current_user.id,
        HealthRecord.blood_pressure.isnot(None)
    ).all()
    
    if blood_pressure_records:
        systolic = []
        diastolic = []
        for record in blood_pressure_records:
            try:
                sys, dia = map(int, record.blood_pressure.split('/'))
                systolic.append(sys)
                diastolic.append(dia)
            except:
                continue
        
        if systolic and diastolic:
            stats['blood_pressure'] = {
                'systolic_avg': sum(systolic) / len(systolic),
                'systolic_max': max(systolic),
                'systolic_min': min(systolic),
                'diastolic_avg': sum(diastolic) / len(diastolic),
                'diastolic_max': max(diastolic),
                'diastolic_min': min(diastolic)
            }
    
    # 计算血糖的平均值、最高值和最低值
    blood_sugar_stats = db.session.query(
        func.avg(HealthRecord.blood_sugar),
        func.max(HealthRecord.blood_sugar),
        func.min(HealthRecord.blood_sugar)
    ).filter(
        HealthRecord.patient_id == current_user.id,
        HealthRecord.blood_sugar.isnot(None)
    ).first()
    
    if blood_sugar_stats[0]:
        stats['blood_sugar'] = {
            'avg': blood_sugar_stats[0],
            'max': blood_sugar_stats[1],
            'min': blood_sugar_stats[2]
        }
    
    # 计算心率的平均值、最高值和最低值
    heart_rate_stats = db.session.query(
        func.avg(HealthRecord.heart_rate),
        func.max(HealthRecord.heart_rate),
        func.min(HealthRecord.heart_rate)
    ).filter(
        HealthRecord.patient_id == current_user.id,
        HealthRecord.heart_rate.isnot(None)
    ).first()
    
    if heart_rate_stats[0]:
        stats['heart_rate'] = {
            'avg': heart_rate_stats[0],
            'max': heart_rate_stats[1],
            'min': heart_rate_stats[2]
        }
    
    # 计算体重的平均值、最高值和最低值
    weight_stats = db.session.query(
        func.avg(HealthRecord.weight),
        func.max(HealthRecord.weight),
        func.min(HealthRecord.weight)
    ).filter(
        HealthRecord.patient_id == current_user.id,
        HealthRecord.weight.isnot(None)
    ).first()
    
    if weight_stats[0]:
        stats['weight'] = {
            'avg': weight_stats[0],
            'max': weight_stats[1],
            'min': weight_stats[2]
        }
    
    return render_template('analysis/health_stats.html', stats=stats) 