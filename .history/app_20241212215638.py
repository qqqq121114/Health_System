from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
import sqlite3
import os
from sqlalchemy import func
from models import db, User, HealthRecord, FollowUp

# 定义记录类型映射
RECORD_TYPES = {
    'MEDICAL_HISTORY': '病史记录',
    'PHYSICAL_EXAM': '体检报告',
    'DAILY_MONITOR': '日常监测'
}

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
login_manager.login_message = '请先登录后再访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 定义常量
PATIENT_STATUS = {
    'NEW': 'new',           # 新患者
    'ACTIVE': 'active',     # 正常就诊
    'FOLLOW_UP': 'follow_up', # 待复诊
}

# 基本路由
@app.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        if current_user.role == 'DOCTOR':
            return redirect(url_for('doctor_home'))
        else:
            return redirect(url_for('health_records'))
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
            
            # 保存到数据库
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
    print(f"当前用户ID: {current_user.id}")
    print(f"当前用户角色: {current_user.role}")
    
    if current_user.role == 'DOCTOR':
        records = HealthRecord.query.join(User, HealthRecord.patient_id == User.id)\
            .filter(User.role == 'PATIENT')\
            .order_by(HealthRecord.created_at.desc()).all()
    else:
        records = HealthRecord.query.filter_by(patient_id=current_user.id)\
            .order_by(HealthRecord.created_at.desc()).all()
    
    print(f"找到记录数量: {len(records)}")
    for record in records:
        print(f"记录ID: {record.id}, 类型: {record.record_type}, 患者ID: {record.patient_id}")
        record.record_type = RECORD_TYPES.get(record.record_type, record.record_type)
    
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
@app.route('/doctor/home')
@login_required
def doctor_home():
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
    
    # 获取待复数量
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
    
    return render_template('doctor_home.html',
                         today_visits=today_visits,
                         follow_up_count=follow_up_count,
                         new_patients_month=new_patients_month,
                         total_patients=total_patients,
                         my_patients=my_patients,
                         recent_records=recent_records)

@app.route('/doctor/add_record', methods=['GET', 'POST'])
@login_required
def doctor_add_record():
    """医生添加记录页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    # 获取患者ID（如果从患者列表页面跳转）
    patient_id = request.args.get('patient_id', type=int)
    patient = None
    if patient_id:
        patient = User.query.filter_by(id=patient_id, role='PATIENT').first()
    
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
                description=request.form.get('description'),
                symptoms=request.form.get('symptoms'),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                medications=request.form.get('medications'),
                height=request.form.get('height', type=float),
                weight=request.form.get('weight', type=float),
                blood_pressure=f"{request.form.get('blood_pressure_sys', '')}/{request.form.get('blood_pressure_dia', '')}",
                heart_rate=request.form.get('heart_rate', type=int),
                blood_sugar=request.form.get('blood_sugar', type=float),
                blood_fat=request.form.get('blood_fat'),
                liver_function=request.form.get('liver_function'),
                kidney_function=request.form.get('kidney_function'),
                temperature=request.form.get('temperature', type=float),
                pulse=request.form.get('pulse', type=int),
                respiratory_rate=request.form.get('respiratory_rate', type=int),
                oxygen_saturation=request.form.get('oxygen_saturation', type=float)
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            # 获取更新后的今日就诊数
            today_date = datetime.now().date()
            today_visits = HealthRecord.query.filter(
                HealthRecord.doctor_id == current_user.id,
                func.date(HealthRecord.record_date) == today_date
            ).count()
            
            flash('健康记录添加成功！', 'success')
            
            # 如果是 AJAX 请求，返回 JSON 响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': '记录添加成功',
                    'today_visits': today_visits
                })
            
            # 如果是普通表单提交，重定向到主页
            return redirect(url_for('doctor_home'))
            
        except Exception as e:
            db.session.rollback()
            flash('添加记录失败，请重试。', 'danger')
            print(f"Error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500
            return redirect(url_for('doctor_add_record'))
    
    return render_template('doctor/add_record.html', patient=patient)

@app.route('/doctor/patient_list')
@login_required
def doctor_patient_list():
    """医生的患者列表页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取筛选参数
    filter_type = request.args.get('filter', 'all')  # all, my_patients
    search_query = request.args.get('search', '')
    
    # 构建查询
    query = User.query.filter_by(role='PATIENT')
    
    # 如果是"我的患者"，只显示有就诊记录的患者
    if filter_type == 'my_patients':
        query = query.join(HealthRecord, User.id == HealthRecord.patient_id)\
            .filter(HealthRecord.doctor_id == current_user.id)\
            .distinct()
    
    # 如果有搜索关键词，添加搜索条件
    if search_query:
        query = query.filter(
            db.or_(
                User.name.like(f'%{search_query}%'),
                User.phone.like(f'%{search_query}%'),
                User.id_number.like(f'%{search_query}%')
            )
        )
    
    # 获取患者列表
    patients = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取统计数据
    total_patients = User.query.filter_by(role='PATIENT').count()
    my_patients = User.query.filter_by(role='PATIENT')\
        .join(HealthRecord, User.id == HealthRecord.patient_id)\
        .filter(HealthRecord.doctor_id == current_user.id)\
        .distinct().count()
    
    # 获取本月新增患者数
    today = datetime.now().date()
    new_patients_month = User.query.filter(
        User.role == 'PATIENT',
        func.extract('month', User.created_at) == today.month,
        func.extract('year', User.created_at) == today.year
    ).count()
    
    # 获取待复诊数量
    follow_up_count = FollowUp.query.filter_by(
        doctor_id=current_user.id,
        status='pending'
    ).count()
    
    # 获取今日就诊数量
    today_visits = HealthRecord.query.filter(
        HealthRecord.doctor_id == current_user.id,
        func.date(HealthRecord.record_date) == today
    ).count()
    
    return render_template('doctor/patient_list.html',
                        patients=patients.items,
                        pages=patients.pages,
                        page=page,
                        total_patients=total_patients,
                        my_patients=my_patients,
                        new_patients_month=new_patients_month,
                        follow_up_count=follow_up_count,
                        today_visits=today_visits,
                        filter_type=filter_type,
                        search_query=search_query)

@app.route('/doctor/view_patient/<int:patient_id>')
@login_required
def doctor_view_patient(patient_id):
    """查看患者详情页面"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    # 获取患者信息
    patient = User.query.filter_by(id=patient_id, role='PATIENT').first_or_404()
    
    # 获取患者的健康记录
    records = HealthRecord.query.filter_by(
        patient_id=patient.id
    ).order_by(
        HealthRecord.created_at.desc()
    ).all()
    
    # 获取患者的最新体检数据
    latest_physical = HealthRecord.query.filter_by(
        patient_id=patient.id,
        record_type='PHYSICAL_EXAM'
    ).order_by(
        HealthRecord.created_at.desc()
    ).first()
    
    # 获取患者的最新日常监测数据
    latest_monitor = HealthRecord.query.filter_by(
        patient_id=patient.id,
        record_type='DAILY_MONITOR'
    ).order_by(
        HealthRecord.created_at.desc()
    ).first()
    
    # 获取患者的复诊记录
    follow_ups = FollowUp.query.filter_by(
        patient_id=patient.id
    ).order_by(
        FollowUp.follow_up_date.desc()
    ).all()
    
    # 获取患者的健康趋势数据
    blood_pressure_data = []
    blood_sugar_data = []
    weight_data = []
    
    for record in records:
        if record.record_type in ['PHYSICAL_EXAM', 'DAILY_MONITOR']:
            record_date = record.record_date.strftime('%Y-%m-%d')
            
            # 血压数据
            if record.blood_pressure:
                try:
                    sys, dia = record.blood_pressure.split('/')
                    blood_pressure_data.append({
                        'date': record_date,
                        'systolic': int(sys),
                        'diastolic': int(dia)
                    })
                except:
                    pass
            
            # 血糖数据
            if record.blood_sugar:
                blood_sugar_data.append({
                    'date': record_date,
                    'value': float(record.blood_sugar)
                })
            
            # 体重数据
            if record.weight:
                weight_data.append({
                    'date': record_date,
                    'value': float(record.weight)
                })
    
    return render_template('doctor/view_patient.html',
                        patient=patient,
                        records=records,
                        latest_physical=latest_physical,
                        latest_monitor=latest_monitor,
                        follow_ups=follow_ups,
                        blood_pressure_data=blood_pressure_data,
                        blood_sugar_data=blood_sugar_data,
                        weight_data=weight_data)

# API路由
@app.route('/api/check_patient/<username>')
@login_required
def check_patient(username):
    """检查患者��息的 API"""
    if current_user.role != 'DOCTOR':
        return jsonify({
            'success': False,
            'message': '无权访问此 API'
        }), 403
    
    try:
        patient = User.query.filter_by(username=username, role='PATIENT').first()
        
        if patient:
            return jsonify({
                'success': True,
                'patient': {
                    'id': patient.id,
                    'username': patient.username,
                    'name': patient.name
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到患者'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/follow_up', methods=['POST'])
@login_required
def add_follow_up():
    """添加复诊记录"""
    if current_user.role != 'DOCTOR':
        return jsonify({
            'success': False,
            'message': '无权进行此操作'
        }), 403
    
    try:
        patient_id = request.form.get('patient_id', type=int)
        follow_up_date = datetime.strptime(request.form.get('follow_up_date'), '%Y-%m-%d')
        reason = request.form.get('reason')
        notes = request.form.get('notes')
        
        # 创建复诊记录
        follow_up = FollowUp(
            patient_id=patient_id,
            doctor_id=current_user.id,
            follow_up_date=follow_up_date,
            reason=reason,
            notes=notes,
            status='pending'
        )
        
        db.session.add(follow_up)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '复诊预约已创建'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/follow_up/<int:follow_up_id>', methods=['POST'])
@login_required
def update_follow_up(follow_up_id):
    """更新复诊状态"""
    if current_user.role != 'DOCTOR':
        return jsonify({
            'success': False,
            'message': '无权操作'
        }), 403
    
    try:
        status = request.form.get('status')
        
        if not status:
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
        
        follow_up = FollowUp.query.get_or_404(follow_up_id)
        
        # 检查是否是该医生的复诊记录
        if follow_up.doctor_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '无权操作此记录'
            }), 403
        
        # 更新状态
        follow_up.status = status
        # 如果是确认完成，更新完成时间
        if status == 'completed':
            follow_up.completed_at = datetime.now()
        
        db.session.commit()
        
        # 获取更新后的待复诊数量
        pending_follow_ups = FollowUp.query.filter_by(
            doctor_id=current_user.id,
            status='pending'
        ).count()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'pending_count': pending_follow_ups
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/follow_up/<int:follow_up_id>/complete', methods=['POST'])
@login_required
def complete_follow_up(follow_up_id):
    """完成复诊"""
    if current_user.role != 'DOCTOR':
        return jsonify({
            'success': False,
            'message': '无权进行此操作'
        }), 403
    
    try:
        follow_up = FollowUp.query.get_or_404(follow_up_id)
        follow_up.status = 'completed'
        follow_up.completed_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '复诊已完成'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/follow_up/<int:follow_up_id>/cancel', methods=['POST'])
@login_required
def cancel_follow_up(follow_up_id):
    """取消复诊"""
    if current_user.role != 'DOCTOR':
        return jsonify({
            'success': False,
            'message': '无权进行此操作'
        }), 403
    
    try:
        follow_up = FollowUp.query.get_or_404(follow_up_id)
        follow_up.status = 'cancelled'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '复诊已取消'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/health_record/<int:record_id>')
@login_required
def get_record(record_id):
    """获取健康记录详情"""
    try:
        record = HealthRecord.query.get_or_404(record_id)
        
        # 检查权限
        if record.patient_id != current_user.id and current_user.role != 'DOCTOR':
            return jsonify({
                'success': False,
                'message': '无权查看此记录'
            }), 403
        
        return jsonify({
            'success': True,
            'record': {
                'id': record.id,
                'record_type': record.record_type,
                'record_date': record.record_date.strftime('%Y-%m-%d'),
                'description': record.description,
                'symptoms': record.symptoms,
                'height': record.height,
                'weight': record.weight,
                'blood_pressure_sys': record.blood_pressure.split('/')[0] if record.blood_pressure else None,
                'blood_pressure_dia': record.blood_pressure.split('/')[1] if record.blood_pressure else None,
                'heart_rate': record.heart_rate,
                'blood_sugar': record.blood_sugar,
                'blood_routine': record.blood_routine,
                'urine_routine': record.urine_routine,
                'liver_function': record.liver_function,
                'kidney_function': record.kidney_function,
                'body_temperature': record.temperature
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    """删除健康记录"""
    try:
        record = HealthRecord.query.get_or_404(record_id)
        
        # 检查权限
        if record.patient_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '无权删除此记录'
            }), 403
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '记录已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/doctor/edit_record/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_health_record(record_id):
    """编辑健康记录"""
    if current_user.role != 'DOCTOR':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))
    
    record = HealthRecord.query.get_or_404(record_id)
    
    # 检查是否是该医生的记录
    if record.doctor_id != current_user.id:
        flash('无权���辑此记录', 'danger')
        return redirect(url_for('doctor_home'))
    
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
            record.liver_function = request.form.get('liver_function')
            record.kidney_function = request.form.get('kidney_function')
            record.temperature = request.form.get('temperature', type=float)
            record.pulse = request.form.get('pulse', type=int)
            record.respiratory_rate = request.form.get('respiratory_rate', type=int)
            record.oxygen_saturation = request.form.get('oxygen_saturation', type=float)
            
            db.session.commit()
            flash('记录更新成功！', 'success')
            return redirect(url_for('doctor_view_patient', patient_id=record.patient_id))
            
        except Exception as e:
            db.session.rollback()
            flash('更新记录失败，请重试。', 'danger')
            print(f"Error: {str(e)}")
    
    return render_template('doctor/edit_record.html', record=record)

@app.route('/add_health_record', methods=['POST'])
@login_required
def add_health_record():
    """用户添加健康记录"""
    print("开始处理添加健康记录请求")
    print(f"当前用户ID: {current_user.id}")
    print(f"当前用户角色: {current_user.role}")
    print(f"请求方法: {request.method}")
    print(f"Content-Type: {request.headers.get('Content-Type')}")
    print(f"表单数据: {request.form}")
    
    if current_user.role != 'PATIENT':
        error_msg = '无权进行此操作'
        print(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 403
        flash(error_msg, 'danger')
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        record_type = request.form.get('record_type')
        if not record_type:
            raise ValueError('记录类型不能为空')
        print(f"记录类型: {record_type}")
        
        # 将中文类型转换为英文存储
        record_type_en = {v: k for k, v in RECORD_TYPES.items()}.get(record_type, record_type)
        print(f"转换后的记录类型: {record_type_en}")
        
        record_date_str = request.form.get('record_date')
        if not record_date_str:
            raise ValueError('记录日期不能为空')
        record_date = datetime.strptime(record_date_str, '%Y-%m-%d')
        
        # 创建新记录
        new_record = HealthRecord(
            patient_id=current_user.id,
            doctor_id=None,  # 初始设置为None，等待医生审核
            record_type=record_type_en,
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
        print("记录添加成功")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '健康记录添加成功！'})
        
        flash('健康记录添加成功！', 'success')
        return redirect(url_for('health_records'))
        
    except ValueError as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"数据验证错误: {error_msg}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(url_for('health_records'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = '添加记录失败，请重试'
        print(f"添加记录失败: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'danger')
        return redirect(url_for('health_records'))

if __name__ == '__main__':
    app.run(debug=True) 