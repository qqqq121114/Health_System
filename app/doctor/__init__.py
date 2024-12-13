from flask import Blueprint

doctor_bp = Blueprint('doctor', __name__)

from . import routes 