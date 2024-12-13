from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        if current_user.role == 'DOCTOR':
            return redirect(url_for('doctor.home'))
        else:
            return redirect(url_for('patient.health_records'))
    return render_template('index.html')

@main_bp.route('/health_education')
@login_required
def health_education():
    """健康教育页面"""
    return render_template('health_education.html')

@main_bp.route('/personal_advice')
@login_required
def personal_advice():
    """个性化建议页面"""
    return render_template('personal_advice.html') 