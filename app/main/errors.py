# -*- coding: utf-8 -*-
from . import main
from flask import make_response, jsonify, g, abort
from enum import Enum
import string


# 错误类型枚举
class Error(Enum):
    UNKNOWN_INTERNAL_ERROR = 500

    FORBIDDEN = 601  # 无权限
    WRONG_PASSWORD = 602  # POST to login 密码错误
    ALREADY_LOGGED_IN = 603  # 用户已登陆,保留
    BAD_TOKEN = 604  # POST to user/getuser token错误
    TOKEN_EXPIRED = 605  # token过期
    ONLY_ACCEPT_JSON = 606  # POST只接受JSON
    FIELD_MISSING = 607  # POST 时缺少必要的参数
    WRONG_FIELD_TYPE = 609  # field类型错误
    UNKNOWN_FIELD = 608  # POST BODY中存在未知field
    BASE64_ERROR = 620  # POST to avatar BASE64字符串错误

    RESOURCE_NOT_FOUND = 700
    USER_NOT_FOUND = 701  # POST to login 用户不存在
    MAIN_COURSE_NOT_FOUND = 702
    SUB_COURSE_NOT_FOUND = 703
    KNOWLEDGE_POINT_NOT_FOUND = 704
    QUESTION_NOT_FOUND = 705
    NOTIFICATION_NOT_FOUND = 706
    SEAT_NOT_FOUND = 707
    TEST_NOT_FOUND = 708
    ROOM_NOT_FOUND = 709
    SCHOOL_NOT_FOUND = 710
    DEPARTMENT_NOT_FOUND = 711
    MAJOR_NOT_FOUND = 712
    CLASS_NOT_FOUND = 713

    RESOURCE_ALREADY_EXISTS = 800
    USER_ALREADY_EXISTS = 801  # POST to register 用户已存在
    MAIN_COURSE_ALREADY_EXISTS = 802  # 主课程已存在
    SUB_COURSE_ALREADY_EXISTS = 803  # 讲台已存在
    KNOWLEDGE_POINT_ALREADY_EXISTS = 804
    QUESTION_ALREADY_EXISTS = 805
    NOTIFICATION_ALREADY_EXISTS = 806
    SEAT_ALREADY_EXISTS = 807
    TEST_ALREADY_EXISTS = 808
    ROOM_ALREADY_EXISTS = 809

    SEAT_ALREADY_TAKEN = 901  # 座位已被别人选中
    SEAT_ALREADY_CHOSEN = 902  # 座位已经选中
    SEAT_ALREADY_FREE_OR_TAKEN = 903  # 座位已空
    SEAT_TOKEN_EXPIRED = 904
    BAD_SEAT_TOKEN = 905
    SEAT_CHOOSING_NOT_AVAILABLE_YET = 906  # 还未到选座时间,需等待
    COURSE_ALREADY_BEGUN = 907  # 课程已经开始,无法选座
    COURSE_IS_NOT_ON_TODAY = 908  # 选择的课程不在今天
    COURSE_ALREADY_OVER = 909  # 课程已经开始,无法选座
    COURSE_NOT_BEGUN = 910
    YOU_ARE_TOO_LATE = 911  # 迟到时间超过上限
    RANDOM_TEST_NOT_SET = 920
    YOU_DO_NOT_HAVE_THIS_COURSE = 921
    YOU_ARE_NOT_THE_TEACHER = 922
    YOU_ARE_NOT_A_STUDENT = 923


# 错误处理,处理Error枚举,统一返回400状态码,接受键值对作为附加错误信息
def handle_error(error_code, **kwargs):
    msg = {'error_msg': "", 'error_code': error_code.value}
    words = string.capwords(error_code.name.replace('_', ' '))
    msg['error_msg'] = words
    for key in kwargs:
        msg[key] = kwargs[key]
    g.msg = msg
    abort(400)


@main.app_errorhandler(200)
def return200(e):
    return ''


@main.app_errorhandler(400)
def error403(e):
    if hasattr(g, 'msg'):
        return make_response(jsonify(g.msg), 400)
    return make_response(jsonify(error_msg='Bad Request', error_code=400), 400)


@main.app_errorhandler(422)
def error422(e):
    return make_response(jsonify({'error_msg': 'Unprocessable Entity', 'error_code': 422}), 422)


@main.app_errorhandler(403)
def error403(e):
    return make_response(jsonify({'error_msg': 'Forbidden', 'error_code': 403}), 403)


@main.app_errorhandler(401)
def error401(e):
    return make_response(jsonify({'error_msg': 'Unauthorized', 'error_code': 401}), 401)


@main.app_errorhandler(406)
def error406(e):
    return make_response(jsonify({'error_msg': 'Only accept JSON', 'error_code': 406}), 406)


@main.app_errorhandler(404)
def error404(e):
    return make_response(jsonify({'error_msg': 'Not Found', 'error_code': 404}), 404)


@main.app_errorhandler(405)
def error405(e):
    return make_response(jsonify({'error_msg': 'Method Not Allowed', 'error_code': 405}), 405)
