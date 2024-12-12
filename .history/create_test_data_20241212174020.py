from app import app, db
from models import User, HealthRecord, FollowUp
from datetime import datetime, timedelta

def create_test_data():
    """创建测试数据"""
    with app.app_context():
        # 清空数据库
        db.drop_all()
        db.create_all()
        
        # 创建医生用户
        doctor = User(
            username='doctor1',
            name='张医生',
            id_number='110101199001011234',
            gender='男',
            phone='13800138000',
            role='DOCTOR'
        )
        doctor.set_password('123456')
        
        # 创建患者用户
        patient1 = User(
            username='patient1',
            name='王大爷',
            id_number='110101193001011234',
            gender='男',
            phone='13900139000',
            role='PATIENT'
        )
        patient1.set_password('123456')
        
        patient2 = User(
            username='patient2',
            name='李奶奶',
            id_number='110101193501011234',
            gender='女',
            phone='13700137000',
            role='PATIENT'
        )
        patient2.set_password('123456')
        
        # 添加用户到数据库
        db.session.add(doctor)
        db.session.add(patient1)
        db.session.add(patient2)
        db.session.commit()
        
        # 创建健康记录
        record1 = HealthRecord(
            patient_id=patient1.id,
            doctor_id=doctor.id,
            record_type='PHYSICAL_EXAM',
            record_date=datetime.now() - timedelta(days=7),
            description='常规体检',
            height=170.0,
            weight=65.0,
            blood_pressure='135/85',
            heart_rate=75,
            blood_sugar=5.6,
            blood_fat='正常',
            liver_function='正常',
            kidney_function='正常'
        )
        
        record2 = HealthRecord(
            patient_id=patient1.id,
            doctor_id=doctor.id,
            record_type='MEDICAL_HISTORY',
            record_date=datetime.now() - timedelta(days=3),
            description='感冒就诊',
            symptoms='咳嗽、发烧',
            diagnosis='普通感冒',
            treatment='建议多休息，多喝水',
            medications='布洛芬、感冒药'
        )
        
        record3 = HealthRecord(
            patient_id=patient2.id,
            doctor_id=doctor.id,
            record_type='DAILY_MONITOR',
            record_date=datetime.now() - timedelta(days=1),
            description='日常监测',
            temperature=36.5,
            pulse=78,
            respiratory_rate=16,
            oxygen_saturation=98.0
        )
        
        # 添加健康记录到数据库
        db.session.add(record1)
        db.session.add(record2)
        db.session.add(record3)
        
        # 创建复诊记录
        follow_up1 = FollowUp(
            patient_id=patient1.id,
            doctor_id=doctor.id,
            follow_up_date=datetime.now() + timedelta(days=7),
            reason='复查感冒症状',
            notes='如果症状未改善需要及时就医'
        )
        
        follow_up2 = FollowUp(
            patient_id=patient2.id,
            doctor_id=doctor.id,
            follow_up_date=datetime.now() + timedelta(days=14),
            reason='定期体检',
            notes='需要空腹'
        )
        
        # 添加复诊记录到数据库
        db.session.add(follow_up1)
        db.session.add(follow_up2)
        
        # 提交所有更改
        db.session.commit()
        
        print('测试数据创建成功！')
        print('医生账号：doctor1 密码：123456')
        print('患者账号：patient1 密码：123456')
        print('患者账号：patient2 密码：123456')

if __name__ == '__main__':
    create_test_data() 