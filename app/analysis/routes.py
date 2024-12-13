from flask import render_template, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import HealthRecord, db
from . import analysis_bp

@analysis_bp.route('/analysis')
@login_required
def index():
    """健康分析首页"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    return render_template('analysis/index.html')

@analysis_bp.route('/analysis/health_trends')
@login_required
def health_trends():
    """健康趋势分析"""
    if current_user.role != 'PATIENT':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    return render_template('analysis/health_trends.html')

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