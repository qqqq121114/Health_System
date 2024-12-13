from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, db
from . import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
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
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """��册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        id_number = request.form.get('id_number')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        role = request.form.get('role')

        # 验证密码是否匹配
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.register'))

        # 验证用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))

        # 验证身份证号是否已存在
        if User.query.filter_by(id_number=id_number).first():
            flash('该身份证号已注册', 'danger')
            return redirect(url_for('auth.register'))

        # 验证手机号是否已存在
        if User.query.filter_by(phone=phone).first():
            flash('该手机号已注册', 'danger')
            return redirect(url_for('auth.register'))

        try:
            # 创建新用户
            user = User(
                username=username,
                name=name,
                id_number=id_number,
                gender=gender,
                phone=phone,
                role=role.upper()  # 存储为大写
            )
            user.set_password(password)
            
            # 保存到数据库
            db.session.add(user)
            db.session.commit()
            
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请稍后重试', 'danger')
            print(f"Registration error: {str(e)}")
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已成功退出登录', 'success')
    return redirect(url_for('index')) 