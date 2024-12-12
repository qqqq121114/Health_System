from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
import sqlite3
import os
from sqlalchemy import func
from models import db, User, HealthRecord

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# 确保数据库目录存在
basedir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(basedir, 'database')
if not os.path.exists(database_dir):
    os.makedirs(database_dir)

# 设置数据库URI
database_path = os.path.join(database_dir, 'health_records.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后再访问此��面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 基本路由
@app.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        if current_user.role == 'DOCTOR':
            # 获取今日日期
            today = datetime.now().date()
            
            # 获取今日记录数
            today_records = HealthRecord.query.filter(
                HealthRecord.doctor_id == current_user.id,
                func.date(HealthRecord.created_at) == today
            ).count()
            
            # 获取本月记录数
            month_records = HealthRecord.query.filter(
                HealthRecord.doctor_id == current_user.id,
                func.extract('month', HealthRecord.created_at) == today.month,
                func.extract('year', HealthRecord.created_at) == today.year
            ).count()
            
            # 获取管理的患者总数
            total_patients = User.query.join(
                HealthRecord, User.id == HealthRecord.patient_id
            ).filter(
                User.role == 'PATIENT',
                HealthRecord.doctor_id == current_user.id
            ).distinct().count()
            
            # 获取最近记录
            recent_records = HealthRecord.query.filter_by(
                doctor_id=current_user.id
            ).order_by(
                HealthRecord.created_at.desc()
            ).limit(5).all()
            
            # 待复诊数量（暂时设为0，后续实现）
            pending_appointments = 0
            
            return render_template('index.html',
                                today_records=today_records,
                                month_records=month_records,
                                total_patients=total_patients,
                                pending_appointments=pending_appointments,
                                recent_records=recent_records)
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        id_number = request.form.get('id_number')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        role = request.form.get('role')

        # 验证密码是否匹配
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))

        # 验证用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))

        # 验证身份证号是否已存在
        if User.query.filter_by(id_number=id_number).first():
            flash('该身份证号已注册', 'danger')
            return redirect(url_for('register'))

        # 验证手机号是否已存在
        if User.query.filter_by(phone=phone).first():
            flash('该手机号已注册', 'danger')
            return redirect(url_for('register'))

        try:
            # 创建新用户
            user = User(
                username=username,
                name=name,
                id_number=id_number,
                gender=gender,
                phone=phone,
                role=role.upper()  # 存储为大写
            )
            user.set_password(password)
            
            # 保存到据库
            db.session.add(user)
            db.session.commit()
            
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请稍后重试', 'danger')
            print(f"Registration error: {str(e)}")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已成功退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/health_records')
@login_required
def health_records():
    """健康记录页面"""
    if current_user.role == 'DOCTOR':
        records = HealthRecord.query.join(User, HealthRecord.patient_id == User.id)\
            .filter(User.role == 'PATIENT')\
            .order_by(HealthRecord.created_at.desc()).all()
    else:
        records = HealthRecord.query.filter_by(patient_id=current_user.id)\
            .order_by(HealthRecord.created_at.desc()).all()
    return render_template('health_records.html', records=records)

@app.route('/health_education')
def health_education():
    """健康教育页面"""
    return render_template('health_education.html')

@app.route('/personal_advice')
@login_required
def personal_advice():
    """个性化建议页面"""
    return render_template('personal_advice.html')

# 医生相关路由
@app.route('/doctor/add_record', methods=['GET', 'POST'])
@login_required
def doctor_add_record():
    """医生添加记录页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # 获取患者信息
            patient_username = request.form.get('patient_username')
            patient = User.query.filter_by(username=patient_username, role='PATIENT').first()
            
            if not patient:
                flash('未找到指定的患者', 'danger')
                return redirect(url_for('doctor_add_record'))
            
            # 获取表单数据
            record_type = request.form.get('record_type')
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d')
            
            # 创建新记录
            new_record = HealthRecord(
                patient_id=patient.id,
                doctor_id=current_user.id,
                record_type=record_type,
                record_date=record_date,
                
                # 通用字段
                description=request.form.get('description'),
                
                # 病史记录字段
                symptoms=request.form.get('symptoms'),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                medications=request.form.get('medications'),
                
                # 体检报告字段
                height=request.form.get('height', type=float),
                weight=request.form.get('weight', type=float),
                blood_pressure=f"{request.form.get('blood_pressure_sys', '')}/{request.form.get('blood_pressure_dia', '')}",
                heart_rate=request.form.get('heart_rate', type=int),
                blood_sugar=request.form.get('blood_sugar', type=float),
                blood_fat=request.form.get('blood_fat'),
                liver_function=request.form.get('liver_function'),
                kidney_function=request.form.get('kidney_function'),
                
                # 日常监测字段
                temperature=request.form.get('temperature', type=float),
                pulse=request.form.get('pulse', type=int),
                respiratory_rate=request.form.get('respiratory_rate', type=int),
                oxygen_saturation=request.form.get('oxygen_saturation', type=float)
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            flash('健康记录添加成功！', 'success')
            return redirect(url_for('doctor_patient_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('添加记录失败，请重试。', 'danger')
            print(f"Error: {str(e)}")
            return redirect(url_for('doctor_add_record'))
    
    return render_template('doctor/add_record.html')

@app.route('/doctor/patient_list')
@login_required
def doctor_patient_list():
    """医生的患者列表页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    patients = User.query.filter_by(role='PATIENT').all()
    return render_template('doctor/patient_list.html', patients=patients)

# API路由
@app.route('/api/check_patient/<username>')
def check_patient(username):
    """检查患者是否存在并返回患者信息"""
    patient = User.query.filter_by(username=username, role='PATIENT').first()
    if patient:
        return jsonify({
            'exists': True,
            'name': patient.name
        })
    return jsonify({
        'exists': False,
        'name': None
    })

if __name__ == '__main__':
    app.run(debug=True) 