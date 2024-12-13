from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# 创建db实例
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    id_number = db.Column(db.String(18), unique=True)
    gender = db.Column(db.String(2))
    phone = db.Column(db.String(11), unique=True)
    role = db.Column(db.String(10))  # DOCTOR or PATIENT
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    health_records = db.relationship('HealthRecord', backref='patient', lazy='dynamic',
                                   foreign_keys='HealthRecord.patient_id')
    doctor_records = db.relationship('HealthRecord', backref='doctor', lazy='dynamic',
                                   foreign_keys='HealthRecord.doctor_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_age(self):
        if not self.id_number or len(self.id_number) != 18:
            return None
        birth_year = int(self.id_number[6:10])
        birth_month = int(self.id_number[10:12])
        birth_day = int(self.id_number[12:14])
        today = datetime.now()
        age = today.year - birth_year
        if (today.month, today.day) < (birth_month, birth_day):
            age -= 1
        return age

class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    record_type = db.Column(db.String(20))  # MEDICAL_HISTORY, PHYSICAL_EXAM, DAILY_MONITOR
    record_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    
    # 体征数据
    height = db.Column(db.Float)  # cm
    weight = db.Column(db.Float)  # kg
    blood_pressure = db.Column(db.String(20))  # 收缩压/舒张压
    heart_rate = db.Column(db.Integer)  # 次/分
    blood_sugar = db.Column(db.Float)  # mmol/L
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)