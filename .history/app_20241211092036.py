from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# 确保数据库目录存在
basedir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(basedir, 'database')
if not os.path.exists(database_dir):
    os.makedirs(database_dir)

# 设置数据库URI
database_path = os.path.join(database_dir, 'health_records.db')

# 如果数据库文件存在，则删除它
if os.path.exists(database_path):
    os.remove(database_path)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后再访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    health_records = db.relationship('HealthRecord', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)
    record_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'record_type': self.record_type,
            'record_date': self.record_date.strftime('%Y-%m-%d'),
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

# 创建所有数据表
with app.app_context():
    db.create_all()

# 认证相关路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请重试', 'danger')
            print(f"Error: {str(e)}")
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'success')
    return redirect(url_for('index'))

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 健康记录相关路由
@app.route('/health_records')
@login_required
def health_records():
    # 只获取当前用户的记录
    records = HealthRecord.query.filter_by(user_id=current_user.id).order_by(HealthRecord.created_at.desc()).all()
    return render_template('health_records.html', records=records)

@app.route('/add_health_record', methods=['POST'])
@login_required
def add_health_record():
    if request.method == 'POST':
        try:
            record_type = request.form.get('record_type')
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d')
            description = request.form.get('description')
            
            new_record = HealthRecord(
                user_id=current_user.id,
                record_type=record_type,
                record_date=record_date,
                description=description
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            flash('健康记录添加成功！', 'success')
        except Exception as e:
            db.session.rollback()
            flash('添加记录失败，请重试。', 'danger')
            print(f"Error: {str(e)}")
            
        return redirect(url_for('health_records'))

@app.route('/get_record/<int:record_id>')
@login_required
def get_record(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    # 确保用户只能访问自己的记录
    if record.user_id != current_user.id:
        return jsonify({'error': '无权访问此记录'}), 403
    return jsonify(record.to_dict())

@app.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    try:
        record = HealthRecord.query.get_or_404(record_id)
        # 确保用户只能删除自己的记录
        if record.user_id != current_user.id:
            return jsonify({'error': '无权删除此记录'}), 403
            
        db.session.delete(record)
        db.session.commit()
        flash('记录已成功删除！', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        flash('删除记录失败，请重试。', 'danger')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health_education')
def health_education():
    return render_template('health_education.html')

@app.route('/personal_advice')
@login_required
def personal_advice():
    return render_template('personal_advice.html')

if __name__ == '__main__':
    app.run(debug=True) 