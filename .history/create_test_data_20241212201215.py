from app import app, db
from models import User, HealthRecord, FollowUp
from datetime import datetime, timedelta
import random

def create_test_data():
    """创建测试数据"""
    with app.app_context():
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
        patients_data = [
            {
                'username': 'patient1',
                'name': '王大爷',
                'id_number': '110101193001011234',
                'gender': '男',
                'age': 75,
                'phone': '13900139001',
                'address': '北京市朝阳区建国路1号',
                'medical_history': '高血压、糖尿病史',
                'allergies': '青霉素过敏',
                'emergency_contact': '王小明',
                'emergency_phone': '13900139002'
            },
            {
                'username': 'patient2',
                'name': '李奶奶',
                'id_number': '110101193501011234',
                'gender': '女',
                'age': 70,
                'phone': '13900139003',
                'address': '北京市海淀区中关村大街1号',
                'medical_history': '冠心病史',
                'allergies': '无',
                'emergency_contact': '李小红',
                'emergency_phone': '13900139004'
            },
            {
                'username': 'patient3',
                'name': '张大叔',
                'id_number': '110101196001011234',
                'gender': '男',
                'age': 65,
                'phone': '13900139005',
                'address': '北京市西城区西单大街1号',
                'medical_history': '胃病史',
                'allergies': '海鲜过敏',
                'emergency_contact': '张小强',
                'emergency_phone': '13900139006'
            },
            {
                'username': 'patient4',
                'name': '赵婆婆',
                'id_number': '110101194001011234',
                'gender': '女',
                'age': 80,
                'phone': '13900139007',
                'address': '北京市东城区王府井大街1号',
                'medical_history': '关节炎、高血压史',
                'allergies': '无',
                'emergency_contact': '赵小梅',
                'emergency_phone': '13900139008'
            }
        ]
        
        patients = []
        for data in patients_data:
            patient = User(
                username=data['username'],
                name=data['name'],
                id_number=data['id_number'],
                gender=data['gender'],
                age=data['age'],
                phone=data['phone'],
                address=data['address'],
                medical_history=data['medical_history'],
                allergies=data['allergies'],
                emergency_contact=data['emergency_contact'],
                emergency_phone=data['emergency_phone'],
                role='PATIENT'
            )
            patient.set_password('123456')
            patients.append(patient)
        
        # 添加用户到数据库
        db.session.add(doctor)
        for patient in patients:
            db.session.add(patient)
        db.session.commit()
        
        # 创建健康记录
        record_types = ['MEDICAL_HISTORY', 'PHYSICAL_EXAM', 'DAILY_MONITOR']
        for patient in patients:
            # 为每个患者创建3-5条记录
            for _ in range(random.randint(3, 5)):
                record_type = random.choice(record_types)
                record_date = datetime.now() - timedelta(days=random.randint(0, 30))
                
                record = HealthRecord(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    record_type=record_type,
                    record_date=record_date,
                    description='常规检查',
                    symptoms='头晕、乏力' if record_type == 'MEDICAL_HISTORY' else None,
                    diagnosis='高血压' if record_type == 'MEDICAL_HISTORY' else None,
                    treatment='建议服用降压药' if record_type == 'MEDICAL_HISTORY' else None,
                    medications='络活喜' if record_type == 'MEDICAL_HISTORY' else None,
                    height=random.uniform(150, 175) if record_type == 'PHYSICAL_EXAM' else None,
                    weight=random.uniform(50, 80) if record_type == 'PHYSICAL_EXAM' else None,
                    blood_pressure=f"{random.randint(110, 150)}/{random.randint(60, 90)}",
                    heart_rate=random.randint(60, 100),
                    blood_sugar=random.uniform(4.0, 7.0),
                    blood_fat='正常' if record_type == 'PHYSICAL_EXAM' else None,
                    liver_function='正常' if record_type == 'PHYSICAL_EXAM' else None,
                    kidney_function='正常' if record_type == 'PHYSICAL_EXAM' else None,
                    temperature=random.uniform(36.3, 37.2) if record_type == 'DAILY_MONITOR' else None,
                    pulse=random.randint(60, 100) if record_type == 'DAILY_MONITOR' else None,
                    respiratory_rate=random.randint(16, 20) if record_type == 'DAILY_MONITOR' else None,
                    oxygen_saturation=random.uniform(95, 100) if record_type == 'DAILY_MONITOR' else None
                )
                db.session.add(record)
        
        # 创建复诊记录
        for patient in patients:
            follow_up = FollowUp(
                patient_id=patient.id,
                doctor_id=doctor.id,
                follow_up_date=datetime.now() + timedelta(days=random.randint(1, 14)),
                reason='复查血压',
                notes='请空腹前来',
                status='pending'
            )
            db.session.add(follow_up)
        
        # 提交所有更改
        db.session.commit()
        
        print('测试数据创建成功！')
        print('\n医生账号：')
        print('用户名: doctor1')
        print('密码: 123456')
        print('\n患者账号：')
        for i in range(len(patients)):
            print(f'用户名: patient{i+1}')
            print('密码: 123456')

if __name__ == '__main__':
    create_test_data() 