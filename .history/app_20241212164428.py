# 定义常量
RECORD_TYPES = {
    'PHYSICAL_EXAM': '体检报告',
    'MEDICAL_HISTORY': '病史记录',
    'DAILY_MONITOR': '日常监测'
}

PATIENT_STATUS = {
    'NEW': 'new',           # 新患者
    'ACTIVE': 'active',     # 正常就诊
    'FOLLOW_UP': 'follow_up', # 待复诊
}

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
from sqlalchemy import func

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

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后再访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='patient')  # 'doctor' or 'patient'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 患者的健康记录
    health_records = db.relationship('HealthRecord', 
                                   backref='patient',
                                   lazy=True,
                                   foreign_keys='HealthRecord.user_id',
                                   cascade='all, delete-orphan')
    
    # 医生创建的记录
    doctor_records = db.relationship('HealthRecord',
                                   backref='doctor',
                                   lazy=True,
                                   foreign_keys='HealthRecord.doctor_id')
    
    # 患者信息字段
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    medical_history = db.Column(db.Text)
    main_symptoms = db.Column(db.Text)
    status = db.Column(db.String(20), default=PATIENT_STATUS['NEW'])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_doctor(self):
        return self.role == 'doctor'
    
    def get_visit_count(self):
        return HealthRecord.query.filter_by(user_id=self.id).count()
    
    def get_last_visit(self):
        last_record = HealthRecord.query.filter_by(user_id=self.id)\
            .order_by(HealthRecord.created_at.desc()).first()
        return last_record.created_at if last_record else None

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    
    # 基本信息
    record_type = db.Column(db.String(50), nullable=False)
    record_date = db.Column(db.DateTime, nullable=False)
    
    # 体征数据
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    blood_pressure_sys = db.Column(db.Integer)
    blood_pressure_dia = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)
    blood_sugar = db.Column(db.Float)
    body_temperature = db.Column(db.Float)
    
    # 实验室检查
    blood_routine = db.Column(db.Text)
    urine_routine = db.Column(db.Text)
    liver_function = db.Column(db.Text)
    kidney_function = db.Column(db.Text)
    blood_lipids = db.Column(db.Text)
    
    # 其他信息
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    medications = db.Column(db.Text)
    description = db.Column(db.Text)
    
    # 记录信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'record_type': self.record_type,
            'record_date': self.record_date.strftime('%Y-%m-%d'),
            'height': self.height,
            'weight': self.weight,
            'blood_pressure_sys': self.blood_pressure_sys,
            'blood_pressure_dia': self.blood_pressure_dia,
            'heart_rate': self.heart_rate,
            'blood_sugar': self.blood_sugar,
            'body_temperature': self.body_temperature,
            'blood_routine': self.blood_routine,
            'urine_routine': self.urine_routine,
            'liver_function': self.liver_function,
            'kidney_function': self.kidney_function,
            'blood_lipids': self.blood_lipids,
            'symptoms': self.symptoms,
            'diagnosis': self.diagnosis,
            'treatment': self.treatment,
            'medications': self.medications,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M')
        }

class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    follow_up_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='follow_ups')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_follow_ups')

def init_db():
    with app.app_context():
        # 只在数据库不存在时创建表
        if not os.path.exists(database_path):
            db.create_all()
            print("数据库已初始化")

# 初始化数据库（只在数据库不存在时创建）
init_db()

# 认证相关路由
@app.route('/login', methods=['GET', 'POST'])
def login():
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
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'patient')  # 获取用户选择的角色
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        # 验证角色是否有效
        if role not in ['patient', 'doctor']:
            flash('无效的用户角色', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请重试', 'danger')
            print(f"Error: {str(e)}")
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'success')
    return redirect(url_for('index'))

# 主页路由
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_doctor():
            # 获取医生相关的数据
            today = datetime.now().date()
            
            # 今日记录数
            today_records = HealthRecord.query.filter(
                HealthRecord.doctor_id == current_user.id,
                func.date(HealthRecord.created_at) == today
            ).count()
            
            # 本月记录数
            month_records = HealthRecord.query.filter(
                HealthRecord.doctor_id == current_user.id,
                func.extract('month', HealthRecord.created_at) == today.month,
                func.extract('year', HealthRecord.created_at) == today.year
            ).count()
            
            # 最近添加的记录
            recent_records = HealthRecord.query\
                .join(User, HealthRecord.user_id == User.id)\
                .filter(HealthRecord.doctor_id == current_user.id)\
                .order_by(HealthRecord.created_at.desc())\
                .limit(5)\
                .all()
            
            # 获取最近的患者
            recent_patients = User.query.join(HealthRecord, User.id == HealthRecord.user_id)\
                .filter(User.role == 'patient',
                       HealthRecord.doctor_id == current_user.id)\
                .group_by(User.id)\
                .order_by(func.max(HealthRecord.created_at).desc())\
                .limit(5)\
                .all()
            
            # 为每个患者添加最后就诊时间
            for patient in recent_patients:
                last_record = HealthRecord.query\
                    .filter(HealthRecord.user_id == patient.id,
                           HealthRecord.doctor_id == current_user.id)\
                    .order_by(HealthRecord.created_at.desc())\
                    .first()
                patient.last_visit = last_record.created_at.strftime('%Y-%m-%d') if last_record else '无记录'
            
            # 统计管理的者总数
            total_patients = User.query.join(HealthRecord, User.id == HealthRecord.user_id)\
                .filter(User.role == 'patient',
                       HealthRecord.doctor_id == current_user.id)\
                .group_by(User.id)\
                .count()
            
            # TODO: 待实现预约功能
            pending_appointments = 0
            
            return render_template('doctor_home.html',
                                 recent_records=recent_records,
                                 recent_patients=recent_patients,
                                 today_records=today_records,
                                 month_records=month_records,
                                 total_patients=total_patients,
                                 pending_appointments=pending_appointments)
        else:
            # 患者首页不需要特殊数据
            return render_template('index.html')
    else:
        # 未登录用户看到的首页
        return render_template('index.html')

# 健康记录相关路由
@app.route('/health_records')
@login_required
def health_records():
    if current_user.is_doctor():
        # 医生可以查看所有记录，但需要显示患者信息
        records = HealthRecord.query.join(User).filter(User.role == 'patient').order_by(HealthRecord.created_at.desc()).all()
        return render_template('doctor/health_records.html', records=records)
    else:
        # 患者只能查看自己的记录
        records = HealthRecord.query.filter_by(user_id=current_user.id).order_by(HealthRecord.created_at.desc()).all()
        return render_template('health_records.html', records=records)

@app.route('/add_health_record', methods=['POST'])
@login_required
def add_health_record():
    if request.method == 'POST':
        try:
            print("接收到的表单数据:", request.form)  # 调试信息
            
            # 获取基本信息
            record_type = request.form.get('record_type')
            record_date_str = request.form.get('record_date')
            
            # 验证记录类型
            if not record_type or record_type not in RECORD_TYPES.values():
                flash('无效的记录类型', 'danger')
                return redirect(url_for('health_records'))
            
            # 验证日期
            if not record_date_str:
                flash('记录日期不能为空', 'danger')
                return redirect(url_for('health_records'))
            
            try:
                record_date = datetime.strptime(record_date_str, '%Y-%m-%d')
            except ValueError:
                flash('日期格式无效', 'danger')
                return redirect(url_for('health_records'))
            
            # 创建新记录
            new_record = HealthRecord(
                user_id=current_user.id,
                record_type=record_type,
                record_date=record_date,
                height=request.form.get('height', type=float),
                weight=request.form.get('weight', type=float),
                blood_pressure_sys=request.form.get('blood_pressure_sys', type=int),
                blood_pressure_dia=request.form.get('blood_pressure_dia', type=int),
                heart_rate=request.form.get('heart_rate', type=int),
                blood_sugar=request.form.get('blood_sugar', type=float),
                body_temperature=request.form.get('body_temperature', type=float),
                blood_routine=request.form.get('blood_routine'),
                urine_routine=request.form.get('urine_routine'),
                liver_function=request.form.get('liver_function'),
                kidney_function=request.form.get('kidney_function'),
                symptoms=request.form.get('symptoms'),
                description=request.form.get('description')
            )
            
            print("准备添加记录:", new_record)  # 调试信息
            
            db.session.add(new_record)
            db.session.commit()
            
            flash('健康记录添加成功！', 'success')
            return redirect(url_for('health_records'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding record: {str(e)}")  # 调试信息
            flash(f'添加记录失败: {str(e)}', 'danger')
            
        return redirect(url_for('health_records'))
    
    return redirect(url_for('health_records'))

@app.route('/get_record/<int:record_id>')
@login_required
def get_record(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    # 确保用户只能访问自己的记录
    if record.user_id != current_user.id:
        return jsonify({'error': '无权访问此记录'}), 403
    return jsonify(record.to_dict())

@app.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    try:
        record = HealthRecord.query.get_or_404(record_id)
        # 确保用户只能删除自己的记录
        if record.user_id != current_user.id:
            return jsonify({'error': '无��删除此记录'}), 403
            
        db.session.delete(record)
        db.session.commit()
        flash('记录已成功删除！', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        flash('删除记录失败，请重试。', 'danger')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health_education')
def health_education():
    return render_template('health_education.html')

@app.route('/personal_advice')
@login_required
def personal_advice():
    return render_template('personal_advice.html')

# 添加医生专用路由
@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('index'))  # 直接重定向到主页

@app.route('/doctor/add_record', methods=['GET', 'POST'])
@login_required
def doctor_add_record():
    if not current_user.is_doctor():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # 获取患者信息
            patient_username = request.form.get('patient_username')
            patient = User.query.filter_by(username=patient_username, role='patient').first()
            
            if not patient:
                flash('未找到指定的患者', 'danger')
                return redirect(url_for('doctor_add_record'))
            
            # 获取表单数据并创建记录
            record_type = request.form.get('record_type')
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d')
            
            # 创建新记录，设置医生ID
            new_record = HealthRecord(
                user_id=patient.id,  # 患者ID
                doctor_id=current_user.id,  # 医生ID
                record_type=record_type,
                record_date=record_date,
                height=request.form.get('height', type=float),
                weight=request.form.get('weight', type=float),
                blood_pressure_sys=request.form.get('blood_pressure_sys', type=int),
                blood_pressure_dia=request.form.get('blood_pressure_dia', type=int),
                heart_rate=request.form.get('heart_rate', type=int),
                blood_sugar=request.form.get('blood_sugar', type=float),
                body_temperature=request.form.get('body_temperature', type=float),
                blood_routine=request.form.get('blood_routine'),
                urine_routine=request.form.get('urine_routine'),
                liver_function=request.form.get('liver_function'),
                kidney_function=request.form.get('kidney_function'),
                blood_lipids=request.form.get('blood_lipids'),
                symptoms=request.form.get('symptoms'),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                medications=request.form.get('medications'),
                description=request.form.get('description')
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            flash('健康记录添加成功！', 'success')
            return redirect(url_for('index'))  # 重定向到主页
            
        except Exception as e:
            db.session.rollback()
            flash('添加记录失败，请重试。', 'danger')
            print(f"Error: {str(e)}")
    
    return render_template('doctor/add_record.html')

# 添加患者状态常量
PATIENT_STATUS = {
    'NEW': 'new',           # 新患者
    'ACTIVE': 'active',     # 正常就诊
    'FOLLOW_UP': 'follow_up', # 待复诊
}

# 添加复诊预约模型
class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    follow_up_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='follow_ups')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_follow_ups')

# 医生相关路由
@app.route('/doctor/patients')
@login_required
def doctor_patient_list():
    if not current_user.is_doctor():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取该医生的所有患者
    patients_query = User.query.join(HealthRecord, User.id == HealthRecord.user_id)\
        .filter(User.role == 'patient',
               HealthRecord.doctor_id == current_user.id)\
        .group_by(User.id)
    
    # 分页
    pagination = patients_query.paginate(page=page, per_page=per_page, error_out=False)
    patients = pagination.items
    
    # 为每个患者添加额外信息
    for patient in patients:
        patient.visit_count = patient.get_visit_count()
        last_visit = patient.get_last_visit()
        patient.last_visit = last_visit.strftime('%Y-%m-%d') if last_visit else '无记录'
    
    # 获取统计数据
    today = datetime.now().date()
    total_patients = patients_query.count()
    
    new_patients_month = User.query.join(HealthRecord, User.id == HealthRecord.user_id)\
        .filter(User.role == 'patient',
               HealthRecord.doctor_id == current_user.id,
               func.extract('month', User.created_at) == today.month,
               func.extract('year', User.created_at) == today.year)\
        .group_by(User.id).count()
    
    follow_up_count = FollowUp.query.filter_by(
        doctor_id=current_user.id,
        status='pending'
    ).count()
    
    today_visits = HealthRecord.query.filter(
        HealthRecord.doctor_id == current_user.id,
        func.date(HealthRecord.created_at) == today
    ).count()
    
    return render_template('doctor/patient_list.html',
                         patients=patients,
                         total_patients=total_patients,
                         new_patients_month=new_patients_month,
                         follow_up_count=follow_up_count,
                         today_visits=today_visits,
                         page=page,
                         pages=pagination.pages)

@app.route('/doctor/add_follow_up', methods=['POST'])
@login_required
def doctor_add_follow_up():
    if not current_user.is_doctor():
        return jsonify({'success': False, 'error': '无权访问'}), 403
    
    try:
        patient_id = request.form.get('patient_id', type=int)
        follow_up_date = datetime.strptime(request.form.get('follow_up_date'), '%Y-%m-%d')
        reason = request.form.get('reason')
        notes = request.form.get('notes')
        
        if not patient_id or not follow_up_date or not reason:
            return jsonify({'success': False, 'error': '缺少必要信息'}), 400
        
        # 创建复诊预约
        follow_up = FollowUp(
            patient_id=patient_id,
            doctor_id=current_user.id,
            follow_up_date=follow_up_date,
            reason=reason,
            notes=notes
        )
        
        # 更新患者状态
        patient = User.query.get(patient_id)
        patient.status = PATIENT_STATUS['FOLLOW_UP']
        
        db.session.add(follow_up)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding follow-up: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/doctor/view_patient/<int:patient_id>')
@login_required
def doctor_view_patient(patient_id):
    if not current_user.is_doctor():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    patient = User.query.get_or_404(patient_id)
    if patient.role != 'patient':
        flash('无效的患者ID', 'danger')
        return redirect(url_for('doctor_patient_list'))
    
    # 获取患者的健康记录
    records = HealthRecord.query.filter_by(user_id=patient_id)\
        .order_by(HealthRecord.created_at.desc()).all()
    
    # 获取复诊记录
    follow_ups = FollowUp.query.filter_by(patient_id=patient_id)\
        .order_by(FollowUp.follow_up_date.desc()).all()
    
    return render_template('doctor/view_patient.html',
                         patient=patient,
                         records=records,
                         follow_ups=follow_ups)

@app.route('/doctor/update_follow_up/<int:follow_up_id>', methods=['POST'])
@login_required
def update_follow_up_status(follow_up_id):
    if not current_user.is_doctor():
        return jsonify({'success': False, 'error': '无权访问'}), 403
    
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status or status not in ['completed', 'cancelled']:
            return jsonify({'success': False, 'error': '无效的状态'}), 400
        
        follow_up = FollowUp.query.get_or_404(follow_up_id)
        
        # 确保只能更新自己创建的复诊记录
        if follow_up.doctor_id != current_user.id:
            return jsonify({'success': False, 'error': '无权修改此记录'}), 403
        
        follow_up.status = status
        
        # 如果完成复诊，更新患者状态为正常
        if status == 'completed':
            patient = User.query.get(follow_up.patient_id)
            patient.status = PATIENT_STATUS['ACTIVE']
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating follow-up: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 