from app import app, db

def init_database():
    with app.app_context():
        print("正在删除所有表...")
        db.drop_all()
        print("正在创建所有表...")
        db.create_all()
        print("数据库初始化完成！")

if __name__ == "__main__":
    init_database() 