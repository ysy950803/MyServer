# -*- coding: utf-8 -*-
from flask import g, request, abort, session, send_from_directory

from .. import main
from . import *
import json
from ...main import *
from mongoengine import EmbeddedDocument, EmbeddedDocumentListField, IntField, ListField, StringField, NotUniqueError
import time


@main.route('/user/login', methods=['POST'])
def user_login(token_only=False):
    get = get_json()
    user_id = get('user_id')
    password = get('password')
    role = get('role')
    user = get_user_with_role(role, user_id, password)
    if isinstance(user, Error):
        handle_error(user)
    if token_only:
        return success_reponse(token=user.generate_token())
    json_dict = user.to_dict_all()
    return success_reponse(user=json_dict, current_week=WEEK_NO, token=user.generate_token())


@main.route('/user/login/getToken', methods=['POST'])
def get_token():
    return user_login(token_only=True)


@main.route('/user/me', methods=['POST'])
@require_token
def get_user():
    return success_reponse(info=g.user.to_dict_all())


@main.route('/user/modifyMe', methods=['POST'])
@require_token
def modify_my_info():
    allowed = ['email', 'gender']
    user = g.user
    modify_from_request_or_422(user, allowed_fields=allowed)
    user.save()
    return success_reponse(user=user.to_dict_all())


@main.route('/user/register/getSchools', methods=['POST'])
def get_schools():
    school_list = []
    schools = School.objects()
    return success_reponse(schools=map(lambda x: {'school_id': x.school_id, 'school_name': x.school_name}, schools))


@main.route('/user/register/getDepartments', methods=['POST'])
def get_departments():
    get = get_json()
    school_id = get('school_id')
    school = get_by_id_or_ERROR(School, school_id)
    return success_reponse(departmens=school.departments)


@main.route('/user/register/getMajors', methods=['POST'])
def get_majors():
    get = get_json()
    school_id = get('school_id')
    school = get_by_id_or_ERROR(School, school_id)
    return success_reponse(majors=school.majors)


@main.route('/user/register/getClasses', methods=['POST'])
def get_classes():
    get = get_json()
    major_id = get('major_id')
    major = get_by_id_or_ERROR(Major, major_id)
    return success_reponse(classes=major.classes)


def register_common(role):
    get = get_json()
    user_id = get('user_id')
    name = get('name')
    password = get('password')
    email = get('email')
    tel = get('tel')
    gender = get('gender')
    temp_user = get_user_with_role(role, user_id)
    if temp_user != Error.USER_NOT_FOUND:
        handle_error(Error.USER_ALREADY_EXISTS)
    user = User()
    user.user_id = user_id
    user.name = name
    user.password = password
    user.email = email
    user.gender = gender
    user.role = role
    user.tel = tel
    return user


@main.route('/user/register/student', methods=['POST'])
def register_student():
    get = get_json()
    class_id = get('class_id')
    major_id = get('major_id')
    class_o = get_by_id_or_ERROR(DClass, class_id)
    major = get_by_id_or_ERROR(Major, major_id)
    if not class_o:
        handle_error(Error.CLASS_NOT_FOUND)
    if not major:
        handle_error(Error.MAJOR_NOT_FOUND)
    base_user = register_common(2)
    user = Student().init_from_user(base_user)
    user.class_name = class_o.class_name
    user.major_name = major.major_name
    user.grade = class_o.grade
    user.save()
    class_o.update(add_to_set__students={'name': user.name, 'student_id': user.user_id})
    return success_reponse()


@main.route('/user/register/teacher', methods=['POST'])
def register_teacher():
    get = get_json()
    dept_id = get('dept_id')
    title = get('title')
    office = get('office')
    dept = get_by_id_or_ERROR(Department, dept_id)
    if not dept:
        handle_error(Error.DEPARTMENT_NOT_FOUND)
    base_user = register_common(1)

    user = Teacher().init_from_user(base_user)
    user.dept_name = dept.dept_id
    user.title = title
    user.office = office

    user.save()
    return success_reponse()


@main.route('/user/registerCourse', methods=['POST'])
@require_token
def register_course():
    course = get_sub_course_pre()
    role = g.user.role
    if role == 1:
        if g.user in course.teachers:
            handle_error(Error.USER_ALREADY_EXISTS)
        course.update(add_to_set__teachers=g.user)
    elif role == 2:
        if g.user in course.students:
            handle_error(Error.USER_ALREADY_EXISTS)
        course.update(add_to_set__students=g.user, add_to_set__classes=g.user.class_name)
    g.user.update(add_to_set__courses=course)
    return success_reponse()


# 头像上传
@main.route('/user/avatar', methods=['POST'])
@require_token
def post_avatar():
    get = get_json()
    img = get('img')
    with open(AVATAR_FOLDER + g.user.user_id + '.jpg', 'w') as file:
        try:
            file.write(img.decode('base64'))
        except:
            handle_error(Error.BASE64_ERROR)
    return success_reponse()


# 头像获取
@main.route('/user/avatar/<user_id>.jpg')
def get_avatar(user_id):
    return send_from_directory(AVATAR_FOLDER, user_id + '.jpg')


@main.route('/getServerTime')
def check_time():
    return success_reponse(server_time=time.time())
