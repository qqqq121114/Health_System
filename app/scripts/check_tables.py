from app import create_app, db
from sqlalchemy import inspect

def check_tables():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("\n=== 数据库中的表 ===")
        for table in tables:
            print(f"表名: {table}")
            columns = inspector.get_columns(table)
            print("列:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
            print()

if __name__ == '__main__':
    check_tables() 