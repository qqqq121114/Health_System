from flask import Flask
from models import db, User, HealthRecord, FollowUp
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/health_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def init_db():
    """初始化数据库"""
    with app.app_context():
        # 删除所有表
        print("正在删除所有表...")
        db.drop_all()
        
        # 创建所有表
        print("正在创建所有表...")
        db.create_all()
        
        print("数据库初始化完成！")

if __name__ == '__main__':
    init_db() 