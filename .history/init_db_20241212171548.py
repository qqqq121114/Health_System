import os
from app import db

# 删除旧的数据库文件（如果存在）
if os.path.exists('health_records.db'):
    os.remove('health_records.db')

# 创建所有表
db.create_all()

print("数据库已重新初始化") 