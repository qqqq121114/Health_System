from flask import Blueprint

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

from . import routes  # 导入routes模块，注册路由 