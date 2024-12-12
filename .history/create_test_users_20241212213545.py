from app import app, db, User

def create_test_users():
    with app.app_context():
        # 创建医生账号
        doctor = User(
            username='doctor1',
            name='张医生',
            id_number='110101199001011234',
            gender='男',
            phone='13800138000',
            role='DOCTOR'
        )
        doctor.set_password('123456')
        
        # 创建患者账号
        patient = User(
            username='patient1',
            name='王患者',
            id_number='110101195001011234',
            gender='男',
            phone='13900139000',
            role='PATIENT'
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