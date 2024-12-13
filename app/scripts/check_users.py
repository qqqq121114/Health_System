import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_users():
    """检查用户信息"""
    from app import create_app
    from app.models import db, User
    
    app = create_app()
    with app.app_context():
        # 查询所有用户
        users = User.query.all()
        print("\n当前用户列表：")
        print("-" * 50)
        for user in users:
            print(f"用户名: {user.username}")
            print(f"姓名: {user.name}")
            print(f"角色: {user.role}")
            print("-" * 50)

if __name__ == '__main__':
    check_users() 