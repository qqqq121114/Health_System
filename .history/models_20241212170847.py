class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(80), nullable=False)  # 真实姓名
    id_number = db.Column(db.String(18), unique=True, nullable=False)  # 身份证号
    gender = db.Column(db.String(10), nullable=False)  # 性别
    phone = db.Column(db.String(11), nullable=False)  # 手机号码
    role = db.Column(db.String(20), nullable=False)  # 用户角色
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    health_records = db.relationship('HealthRecord', backref='patient', lazy=True,
                                   foreign_keys='HealthRecord.patient_id')
    doctor_records = db.relationship('HealthRecord', backref='doctor', lazy=True,
                                   foreign_keys='HealthRecord.doctor_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>' 