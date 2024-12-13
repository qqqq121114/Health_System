from flask import render_template, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import HealthRecord, db
from . import analysis_bp

def calculate_health_score(records):
    """计算总体健康评分"""
    if not records:
        return None
    
    # 这里实现健康评分的计算逻辑
    # TODO: 实现更复杂的评分算法
    return 85

def analyze_blood_pressure(bp_str):
    """分析血压状态"""
    if not bp_str:
        return None, 0
    
    try:
        sys, dia = map(int, bp_str.split('/'))
        if sys < 120 and dia < 80:
            return 'normal', 100
        elif sys < 140 and dia < 90:
            return 'elevated', 80
        else:
            return 'high', 60
    except:
        return None, 0

def analyze_blood_sugar(value):
    """分析血糖状态"""
    if not value:
        return None, 0
    
    try:
        value = float(value)
        if 3.9 <= value <= 6.1:
            return 'normal', 100
        elif 6.1 < value <= 7.0:
            return 'elevated', 70
        else:
            return 'high', 50
    except:
        return None, 0

def calculate_bmi(weight, height):
    """计算BMI指数"""
    if not weight or not height:
        return None, 0
    
    try:
        height_m = float(height) / 100
        bmi = float(weight) / (height_m * height_m)
        if 18.5 <= bmi <= 24.9:
            return 'normal', 100
        elif 24.9 < bmi <= 29.9:
            return 'overweight', 70
        else:
            return 'obese', 50
    except:
        return None, 0

def get_trend_data(patient_id, days=7):
    """获取健康趋势数据"""
    start_date = datetime.now().date() - timedelta(days=days)
    records = HealthRecord.query.filter(
        HealthRecord.patient_id == patient_id,
        HealthRecord.record_date >= start_date
    ).order_by(HealthRecord.record_date.asc()).all()

    dates = []
    blood_pressure_sys = []
    blood_pressure_dia = []
    blood_sugar = []
    heart_rate = []
    weight = []

    for record in records:
        dates.append(record.record_date.strftime('%Y-%m-%d'))
        
        # 处理血压数据
        if record.blood_pressure:
            try:
                sys, dia = map(int, record.blood_pressure.split('/'))
                blood_pressure_sys.append(sys)
                blood_pressure_dia.append(dia)
            except:
                blood_pressure_sys.append(None)
                blood_pressure_dia.append(None)
        else:
            blood_pressure_sys.append(None)
            blood_pressure_dia.append(None)
        
        # 处理其他数据
        blood_sugar.append(float(record.blood_sugar) if record.blood_sugar else None)
        heart_rate.append(int(record.heart_rate) if record.heart_rate else None)
        weight.append(float(record.weight) if record.weight else None)

    return {
        'dates': dates,
        'blood_pressure_sys': blood_pressure_sys,
        'blood_pressure_dia': blood_pressure_dia,
        'blood_sugar': blood_sugar,
        'heart_rate': heart_rate,
        'weight': weight
    }

@analysis_bp.route('/analysis')
@login_required
def index():
    """健康分析首页"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取最新的健康记录
    latest_record = HealthRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(HealthRecord.record_date.desc()).first()
    
    # 获取最近一周的记录
    week_ago = datetime.now().date() - timedelta(days=7)
    recent_records = HealthRecord.query.filter(
        HealthRecord.patient_id == current_user.id,
        HealthRecord.record_date >= week_ago
    ).order_by(HealthRecord.record_date.asc()).all()
    
    # 计算健康状态
    blood_pressure_status, blood_pressure_percentage = analyze_blood_pressure(
        latest_record.blood_pressure if latest_record else None
    )
    
    blood_sugar_status, blood_sugar_percentage = analyze_blood_sugar(
        latest_record.blood_sugar if latest_record else None
    )
    
    bmi_status, bmi_percentage = calculate_bmi(
        latest_record.weight if latest_record else None,
        latest_record.height if latest_record else None
    )
    
    health_score = calculate_health_score(recent_records)
    
    # 健康风险评估
    health_risks = []
    if latest_record:
        if blood_pressure_status == 'high':
            health_risks.append({
                'name': '高血压风险',
                'description': '您的血压水平偏高，建议及时就医',
                'level': 'danger',
                'icon': 'heart',
                'score': 75
            })
        if blood_sugar_status == 'high':
            health_risks.append({
                'name': '血糖异常',
                'description': '血糖水平超出正常范围，需要注意',
                'level': 'warning',
                'icon': 'tint',
                'score': 65
            })
    
    # 健康建议
    health_advice = []
    if latest_record:
        if blood_pressure_status != 'normal':
            health_advice.append({
                'title': '控制血压',
                'content': '建议减少盐分摄入，保持规律运动',
                'type': 'primary',
                'icon': 'heart'
            })
        if blood_sugar_status != 'normal':
            health_advice.append({
                'title': '血糖管理',
                'content': '注意饮食控制，避免高糖食物',
                'type': 'success',
                'icon': 'apple-alt'
            })
        if bmi_status != 'normal':
            health_advice.append({
                'title': '体重管理',
                'content': '建议适量运动，保持健康饮食',
                'type': 'warning',
                'icon': 'running'
            })
    
    # 健康统计
    health_stats = []
    if recent_records:
        # 血压统计
        bp_values = [r.blood_pressure for r in recent_records if r.blood_pressure]
        if bp_values:
            latest_bp = bp_values[-1]
            prev_bp = bp_values[-2] if len(bp_values) > 1 else None
            if prev_bp:
                try:
                    latest_sys = int(latest_bp.split('/')[0])
                    prev_sys = int(prev_bp.split('/')[0])
                    trend = latest_sys - prev_sys
                    health_stats.append({
                        'name': '平均血压',
                        'period': '最近7天',
                        'value': latest_bp,
                        'trend_value': f'{abs(trend)}mmHg',
                        'trend_color': 'danger' if trend > 0 else 'success',
                        'trend_icon': 'arrow-up' if trend > 0 else 'arrow-down'
                    })
                except:
                    pass
        
        # 血糖统计
        sugar_values = [r.blood_sugar for r in recent_records if r.blood_sugar]
        if sugar_values:
            avg_sugar = sum(sugar_values) / len(sugar_values)
            health_stats.append({
                'name': '平均血糖',
                'period': '最近7天',
                'value': f'{avg_sugar:.1f}',
                'trend_value': '正常范围',
                'trend_color': 'success',
                'trend_icon': 'check'
            })
    
    return render_template('analysis/index.html',
        blood_pressure_status=blood_pressure_status,
        blood_pressure_percentage=blood_pressure_percentage,
        blood_sugar_status=blood_sugar_status,
        blood_sugar_percentage=blood_sugar_percentage,
        bmi_status=bmi_status,
        bmi_percentage=bmi_percentage,
        health_score=health_score,
        health_risks=health_risks,
        health_advice=health_advice,
        health_stats=health_stats
    )

@analysis_bp.route('/analysis/health_trends')
@login_required
def health_trends():
    """健康趋势分析"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取趋势数据
    trend_data = get_trend_data(current_user.id)
    
    return render_template('analysis/health_trends.html',
        trend_data=trend_data
    )

@analysis_bp.route('/analysis/risk_assessment')
@login_required
def risk_assessment():
    """健康风险评估"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    return render_template('analysis/risk_assessment.html')

@analysis_bp.route('/analysis/health_stats')
@login_required
def health_stats():
    """健康统计分析"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    return render_template('analysis/health_stats.html') 