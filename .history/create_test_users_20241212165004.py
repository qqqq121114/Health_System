from app import app, db, User

def create_test_users():
    with app.app_context():
        # 创建医生账号
        doctor = User(
            username='doctor1',
            email='doctor1@example.com',
            role='doctor'
        )
        doctor.set_password('123456')
        
        # 创建患者账号
        patient = User(
            username='patient1',
            email='patient1@example.com',
            role='patient',
            age=65,
            gender='男',
            phone='13800138000',
            address='北京市朝阳区',
            medical_history='高血压、糖尿病史',
            main_symptoms='偶有头晕'
        )
        patient.set_password('123456')
        
        # 添加到数据库
        db.session.add(doctor)
        db.session.add(patient)
        
        try:
            db.session.commit()
            print("测试用户创建成功！")
            print("\n医生账号:")
            print("用户名: doctor1")
            print("密码: 123456")
            print("\n患者账号:")
            print("用户名: patient1")
            print("密码: 123456")
        except Exception as e:
            db.session.rollback()
            print(f"创建用户失败: {str(e)}")

if __name__ == "__main__":
    create_test_users() 