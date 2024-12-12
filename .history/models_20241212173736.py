from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(80), nullable=False)  # 真实姓名
    id_number = db.Column(db.String(18), unique=True, nullable=False)  # 身份证号
    gender = db.Column(db.String(10), nullable=False)  # 性别
    phone = db.Column(db.String(11), nullable=False)  # 手机号码
    role = db.Column(db.String(20), nullable=False)  # 用户角色
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    health_records = db.relationship('HealthRecord', backref='patient', lazy=True,
                                   foreign_keys='HealthRecord.patient_id')
    doctor_records = db.relationship('HealthRecord', backref='doctor', lazy=True,
                                   foreign_keys='HealthRecord.doctor_id')
    follow_ups = db.relationship('FollowUp', backref='patient', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_doctor(self):
        return self.role == 'DOCTOR'

    def get_visit_count(self):
        """获取就诊次数"""
        return HealthRecord.query.filter_by(patient_id=self.id).count()

    def get_last_visit(self):
        """获取最近就诊时间"""
        last_record = HealthRecord.query.filter_by(patient_id=self.id)\
            .order_by(HealthRecord.created_at.desc()).first()
        return last_record.created_at if last_record else None

    def __repr__(self):
        return f'<User {self.username}>'

class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # 记录类型（病史记录/体检报告/日常监测）
    record_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 通用字段
    description = db.Column(db.Text)  # 描述/备注
    
    # 病史记录字段
    symptoms = db.Column(db.Text)  # 症状
    diagnosis = db.Column(db.Text)  # 诊断
    treatment = db.Column(db.Text)  # 治疗方案
    medications = db.Column(db.Text)  # 用药情况
    
    # 体检报告字段
    height = db.Column(db.Float)  # 身高
    weight = db.Column(db.Float)  # 体重
    blood_pressure = db.Column(db.String(20))  # 血压
    heart_rate = db.Column(db.Integer)  # 心率
    blood_sugar = db.Column(db.Float)  # 血糖
    blood_fat = db.Column(db.Text)  # 血脂
    liver_function = db.Column(db.Text)  # 肝功能
    kidney_function = db.Column(db.Text)  # 肾功能
    
    # 日常监测字段
    temperature = db.Column(db.Float)  # 体温
    pulse = db.Column(db.Integer)  # 脉搏
    respiratory_rate = db.Column(db.Integer)  # 呼吸频率
    oxygen_saturation = db.Column(db.Float)  # 血氧饱和度
    
    def __repr__(self):
        return f'<HealthRecord {self.id}>'

class FollowUp(db.Model):
    """复诊记录"""
    __tablename__ = 'follow_ups'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    follow_up_date = db.Column(db.DateTime, nullable=False)  # 预约复诊日期
    reason = db.Column(db.Text, nullable=False)  # 复诊原因
    notes = db.Column(db.Text)  # 备注说明
    status = db.Column(db.String(20), default='pending')  # 状态：pending/completed/cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)  # 完成时间
    
    def __repr__(self):
        return f'<FollowUp {self.id}>'