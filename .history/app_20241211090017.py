from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

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

# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)
    record_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 创建所有数据表
with app.app_context():
    db.create_all()

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health_records')
def health_records():
    records = HealthRecord.query.all()
    return render_template('health_records.html', records=records)

@app.route('/health_education')
def health_education():
    return render_template('health_education.html')

@app.route('/personal_advice')
def personal_advice():
    return render_template('personal_advice.html')

if __name__ == '__main__':
    app.run(debug=True) 