# -*- coding: utf-8 -*-
from app.main.errors import *
from app.Models.user_models import *
from app.Models.gerenal_models import *
from app.Models.course_models import *
from flask import g, request, abort, make_response, jsonify, Response
from functools import wraps
from mongoengine import ReferenceField, Q
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
from ...Models import no_dereference_id_only


PER_PAGE = 5


# 获取POST参数中的课程编号和讲台编号,获取课程并返回,找不到则404
def get_sub_course_pre():
    get = get_json()
    course_id = get('course_id')
    sub_id = get('sub_id')
    return get_by_id_or_ERROR(SubCourse, course_id + '#' + sub_id)


def get_user_pre():
    if hasattr(g, 'user'):
        return
    json = request.get_json()
    if not json:
        abort(406)
    get = get_json()
    credential = User.decrypt_token(get('token'))
    if isinstance(credential, Error):
        handle_error(credential)
    user = get_user_with_role(credential['role'], credential['user_id'])
    if isinstance(user, Error):
        handle_error(user)
    g.user = user


# 使用此修饰器的View都需要验证token
def require_token(func):
    @wraps(func)
    def require_func(*args, **kwargs):
        get_user_pre()
        return func(*args, **kwargs)

    return require_func


def get_json():
    json = request.get_json()
    if not json:
        abort(406)

    def get_field(field, allow_none=False):
        value = json.get(field)
        if value is None and not allow_none:
            handle_error(Error.FIELD_MISSING, field=field)
        return value

    return get_field


def instantiate_from_request_or_422(cls, *exceptions, **extra_attrs):
    get = get_json()
    instance = cls()
    fields = dict(cls._fields)

    def get_and_field(field):
        attr = getattr(cls, field)
        if (field not in exceptions) and (field not in extra_attrs) and (
                    attr.required and not attr.primary_key) and (attr.default is None):
            value = get(field)
            setattr(instance, field, value)

    def set_field((key, value)):
        setattr(instance, key, value)

    map(get_and_field, fields)
    map(set_field, extra_attrs.items())
    return instance


def parse_type_string(instance):
    type_o = type(instance)
    if type_o == unicode:
        return 'String'
    if type_o == int:
        return 'Int'
    if type_o == bool:
        return 'Boolean'
    if type_o == dict:
        return 'Dict'
    if type_o == list:
        return 'List'
    return ''


def modify_from_request_or_422(instance, allowed_fields, exceptions, **extra_attrs):
    json = request.get_json()
    json.pop('token', None)
    fields = dict(instance._fields)
    cls = type(instance)
    exceptions.append('token')
    def get_and_try_setting((key, value)):
        if key in exceptions:
            return
        if not hasattr(cls, key):
            handle_error(Error.UNKNOWN_FIELD, field=key)
        if key not in allowed_fields:
            handle_error(Error.FORBIDDEN)
        attr = getattr(instance, key)
        if type(attr) == type(value):
            setattr(instance, key, value)
        else:
            handle_error(Error.WRONG_FIELD_TYPE, field=key, should_be=parse_type_string(attr))

    def set_field((key, value)):
        setattr(instance, key, value)

    map(get_and_try_setting, json.items())
    map(set_field, extra_attrs.items())


def require_is_teacher(func):
    @wraps(func)
    def require(*args, **kwargs):
        get_user_pre()
        if not g.user.role == 1:
            handle_error(Error.YOU_ARE_NOT_THE_TEACHER)
        return func(*args, **kwargs)

    return require


def require_is_student(func):
    @wraps(func)
    def require(*args, **kwargs):
        get_user_pre()
        if not g.user.role == 2:
            handle_error(Error.YOU_ARE_NOT_A_STUDENT)
        return func(*args, **kwargs)

    return require


def require_having_sub_course(func):
    @wraps(func)
    def require(*args, **kwargs):
        get_user_pre()
        course = get_sub_course_pre()
        g.sub_course = course
        if g.user.role == 1:
            if g.user.user_id not in no_dereference_id_only(course.teachers):
                handle_error(Error.YOU_DO_NOT_HAVE_THIS_COURSE)
        elif g.user.role == 2:
            if g.user.user_id not in no_dereference_id_only(course.students):
                handle_error(Error.YOU_DO_NOT_HAVE_THIS_COURSE)
        return func(*args, **kwargs)

    return require


def require_having_main_course(func):
    @wraps(func)
    def require(*args, **kwargs):
        get_user_pre()
        course = get_sub_course_pre()
        course_id = course.course_id
        g.sub_course = course
        g.main_course = course.main_course
        if g.user.role == 1:
            if g.user.user_id not in no_dereference_id_only(course.teachers):
                handle_error(Error.YOU_DO_NOT_HAVE_THIS_COURSE)
        elif g.user.role == 2:
            if g.user.user_id not in no_dereference_id_only(course.students):
                handle_error(Error.YOU_DO_NOT_HAVE_THIS_COURSE)
        return func(*args, **kwargs)

    return require


def require_seat_token(func):
    @wraps(func)
    def require(*args, **kwargs):
        get_user_pre()
        get = get_json()
        r = g.user.validate_seat_token(get('seat_token'))
        if isinstance(r, Error):
            handle_error(r)
        return func(period_num=r)

    return require


def get_main_course_pre():
    get = get_json()
    course_id = get('course_id')
    course = Course.objects(course_id=course_id).first()
    return course


def get_by_id_or_ERROR(cls, id, error=None):
    try:
        return cls.objects.get(pk=id)
    except (DoesNotExist, ValidationError):
        if error is None:
            handle_error(Error.RESOURCE_NOT_FOUND)
        handle_error(error)


# OK的Response,接受键值对作为附加信息
def success_reponse(*args, **kwargs):
    msg = {'msg': 'Success'}
    for arg in args:
        msg.update(arg)
    for key in kwargs:
        msg[key] = kwargs[key]

    return make_response(jsonify(msg), 200)
