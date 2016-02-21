from flask import Blueprint
main = Blueprint('main',__name__)
import errors
from Views import basic_views, import_views, course_views, test_views
