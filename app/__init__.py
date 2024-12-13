from flask import Flask
from flask_login import LoginManager
import os

# 初始化登录管理器
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['DEBUG'] = True
    
    # 确保数据库目录存在
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_dir = os.path.join(basedir, '..', 'instance')
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    
    # 设置数据库URI
    database_path = os.path.join(database_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 导入并初始化数据库
    from .models import db, User
    db.init_app(app)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录后再访问此页面'
    login_manager.login_message_category = 'info'
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        # 注册蓝图
        from .auth import auth_bp
        from .doctor import doctor_bp
        from .patient import patient_bp
        from .routes import main_bp
        from .analysis import analysis_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(doctor_bp)
        app.register_blueprint(patient_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(analysis_bp)
        
        # 创建数据库表
        db.create_all()
    
    return app