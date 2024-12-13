import os
import sys
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_test_data():
    """创建测试用户和健康记录数据"""
    from app import create_app
    from app.models import db, User, HealthRecord
    
    app = create_app()
    with app.app_context():
        print("开始创建测试数据...")
        
        try:
            # 获取或创建测试医生
            doctor = User.query.filter_by(username='doctor1').first()
            if not doctor:
                doctor = User(
                    username='doctor1',
                    name='张医生',
                    id_number='110101199001011234',
                    gender='男',
                    phone='13800138000',
                    role='DOCTOR'
                )
                doctor.set_password('123456')
                db.session.add(doctor)
                print("创建医生账号成功")

            # 获取或创建测试患者
            patient = User.query.filter_by(username='patient1').first()
            if not patient:
                patient = User(
                    username='patient1',
                    name='王患者',
                    id_number='110101195001011234',
                    gender='男',
                    phone='13900139000',
                    role='PATIENT'
                )
                patient.set_password('123456')
                db.session.add(patient)
                print("创建患者账号成功")

            # 提交用户创建
            db.session.commit()
            print("用户创建/更新成功")

            # 删除现有的测试记录
            HealthRecord.query.filter_by(patient_id=patient.id).delete()
            db.session.commit()
            print("已清除现有健康记录")

            # 生成90天的测试数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            current_date = start_date
            records_count = 0

            while current_date <= end_date:
                # 随机生成一些数据波动
                systolic = random.randint(110, 150)  # 收缩压
                diastolic = random.randint(60, 95)   # 舒张压
                blood_sugar = round(random.uniform(4.0, 8.0), 1)  # 血糖
                heart_rate = random.randint(55, 105)  # 心率
                weight = round(random.uniform(65.0, 75.0), 1)  # 体重

                # 创建健康记录
                record = HealthRecord(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    record_type='DAILY_MONITOR',
                    record_date=current_date,
                    blood_pressure=f"{systolic}/{diastolic}",
                    blood_sugar=blood_sugar,
                    heart_rate=heart_rate,
                    weight=weight,
                    height=170.0,  # 身高保持不变
                    description="日常监测记录"
                )

                db.session.add(record)
                current_date += timedelta(days=1)
                records_count += 1

            # 提交所有健康记录
            db.session.commit()
            print(f"测试健康记录数据创建成功！")
            print(f"为患者 {patient.name} 创建了 {records_count} 条健康记录")

        except Exception as e:
            db.session.rollback()
            print(f"创建测试数据失败: {str(e)}")
            raise

if __name__ == '__main__':
    create_test_data() 