from app import create_app, db
from sqlalchemy import inspect
from app.models import HealthRecord

def check_db_structure():
    app = create_app()
    with app.app_context():
        # 检查健康记录的日期格式
        records = HealthRecord.query.all()
        print("\n=== 健康记录日期格式检查 ===")
        for record in records:
            print(f"ID: {record.id}")
            print(f"记录日期: {record.record_date}")
            print(f"记录类型: {record.record_type}")
            print("---")

if __name__ == '__main__':
    check_db_structure() 