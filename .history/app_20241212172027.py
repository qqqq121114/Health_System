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
login_manager.login_message = '请先登录后再访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

if __name__ == '__main__':
    app.run(debug=True) 