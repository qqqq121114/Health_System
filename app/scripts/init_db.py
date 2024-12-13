import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def init_db():
    """初始化数据库"""
    from app import create_app
    from app.models import db
    
    app = create_app()
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("数据库表创建成功！")

if __name__ == '__main__':
    init_db() 