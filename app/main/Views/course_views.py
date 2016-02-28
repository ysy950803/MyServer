# -*- coding: utf-8 -*-
from . import *
import datetime
import json

ALLOWED_SEAT_IN_ADVANCED_SECONDS = 1200


def check_if_able_to_choose_seat(course, period):
    allow_late = course.settings.allow_late
    remaining_seconds_before_beginning = period.get_remaining_seconds_before_beginning()
    if remaining_seconds_before_beginning > ALLOWED_SEAT_IN_ADVANCED_SECONDS:
        return -1, remaining_seconds_before_beginning - ALLOWED_SEAT_IN_ADVANCED_SECONDS  # 还未开始
    elif remaining_seconds_before_beginning > 0:
        return 0, 0  # 可以选座, 未迟到
    if remaining_seconds_before_beginning == -1:
        return Error.COURSE_ALREADY_OVER, 0
    if remaining_seconds_before_beginning == 0:
        past_seconds = period.get_past_seconds()
        if past_seconds > allow_late:
            return Error.YOU_ARE_TOO_LATE, past_seconds
        return 1, past_seconds


@main.route('/seat/getSeatToken', methods=['POST'])
@require_having_sub_course
def get_seat_token():
    course = g.sub_course
    today = TeachDay.get_now_teach_day()
    period = TeachDay.is_course_on_day_and_get_period(course, today)
    if not period:
        handle_error(Error.COURSE_IS_NOT_ON_TODAY)
    access_type, remaining_or_past_secs = check_if_able_to_choose_seat(course=course, period=period)
    if isinstance(access_type, Error):
        handle_error(access_type, late_secs=remaining_or_past_secs)
    if access_type == -1:
        handle_error(Error.SEAT_CHOOSING_NOT_AVAILABLE_YET,
                     remaining_secs=remaining_or_past_secs)
    return success_reponse(room_id=period.room_id,
                           seat_token=g.user.generate_seat_token(period=period.num, late_secs=remaining_or_past_secs,
                                                                 combined_id=course.combined_id),
                           seat_map_token=g.user.generate_seat_map_token(period=period.num,
                                                                         room_id=period.room_id,
                                                                         combined_id=course.combined_id),
                           late_secs=remaining_or_past_secs)


@main.route('/seat/getSeatMapToken', methods=['POST'])
@require_having_sub_course
def get_seat_map_token():
    course = g.sub_course
    today = TeachDay.get_now_teach_day()
    period = TeachDay.is_course_on_day_and_get_period(course, today)
    if not period:
        handle_error(Error.COURSE_IS_NOT_ON_TODAY)
    remaining_secs = period.get_remaining_seconds_before_beginning()
    if remaining_secs > 0:
        handle_error(Error.COURSE_NOT_BEGUN)
    return success_reponse(seat_map_token=g.user.generate_seat_map_token(period=period.num, room_id=period.room_id,
                                                                         combined_id=course.combined_id))


def validate_seat_map_token():
    get = get_json()
    get_user_pre()
    token = get('seat_map_token')
    r = g.user.validate_seat_map_token(token)
    if isinstance(r, Error):
        handle_error(r)
    return r


@main.route('/seat/getSeatMap', methods=['POST'])
def get_seats_in_room():
    get = get_json()
    check_final = get('check_final')
    credential = validate_seat_map_token()
    room = get_by_id_or_ERROR(Room, credential['room_id'])
    is_final = False
    if check_final:
        combined_id = credential['combined_id']
        course = get_by_id_or_ERROR(SubCourse, combined_id)
        period = Period.get_period(credential['period'])
        access_type, secs = check_if_able_to_choose_seat(course, period)
        if isinstance(access_type, Error):
            is_final = True
    return success_reponse(
        seats=room.get_seats_dict(period=credential['period'], show_late_secs=credential['role'] == 1),
        row_num=room.row,
        col_num=room.col, is_final=is_final)


@main.route('/seat/getSeatMapPreview', methods=['POST'])
@require_token
def get_seat_map_preview():
    get = get_json()
    room_id = get('room_id')
    room = get_by_id_or_ERROR(Room, room_id, error=Error.ROOM_NOT_FOUND)
    return success_reponse(seats=room.get_seats_dict(preview=True), row=room.row, col=room.col)


@main.route('/seat/resetSeatMap', methods=['POST'])
@require_is_teacher
@require_having_sub_course
def reset_seat_map():
    course = g.sub_course
    today = TeachDay.get_now_teach_day()
    period = TeachDay.is_course_on_day_and_get_period(course, today)
    if not period:
        handle_error(Error.COURSE_IS_NOT_ON_TODAY)
    remaining_secs_before_beginning = period.remaining_secs_before_beginning()

    room_id = period.room_id
    period_num = str(period.num)
    Seat.objects(room_id=room_id).update(**{'students__' + period_num: '', 'late_secs__' + period_num: 0})
    return success_reponse()


def validate_seat_token():
    get_user_pre()
    token = get_json()('seat_token')
    credential = g.user.validate_seat_token(seat_token=token)
    if isinstance(credential, Error):
        handle_error(credential)
    return credential


@main.route('/seat/chooseSeat', methods=['POST'])
# @require_having_sub_course
def choose_seat():
    credential = validate_seat_token()
    period_num = credential['period']
    combined_id = credential['combined_id']
    late_secs = credential['late_secs']
    period = Period.get_period(period_num)
    course = get_by_id_or_ERROR(SubCourse, combined_id, error=Error.SUB_COURSE_NOT_FOUND)
    access_type, remaining_or_past_secs = check_if_able_to_choose_seat(course=course, period=period)
    if isinstance(access_type, Error):
        handle_error(access_type, late_secs=remaining_or_past_secs)
    if access_type == -1:
        handle_error(Error.SEAT_CHOOSING_NOT_AVAILABLE_YET,
                     remaining_secs=remaining_or_past_secs)
    get = get_json()
    seat_id = get('seat_id')
    seat = get_by_id_or_ERROR(Seat, seat_id, error=Error.SEAT_NOT_FOUND)
    stu_id = g.user.user_id
    if seat.modify({'students__' + str(period_num) + '__in': [None, '']},
                   **{'students__' + str(period_num): stu_id, 'late_secs__' + str(period_num): late_secs}):
        return success_reponse(seat_id=seat_id)
    handle_error(Error.SEAT_ALREADY_TAKEN, seat_id=seat_id, taken_by=seat.students[str(period_num)])


@main.route('/seat/freeSeat', methods=['POST'])
def free_seat():
    credential = validate_seat_token()
    period_num = credential['period']
    combined_id = credential['combined_id']
    late_secs = credential['late_secs']
    period = Period.get_period(period_num)
    course = get_by_id_or_ERROR(SubCourse, combined_id, error=Error.SUB_COURSE_NOT_FOUND)
    access_type, remaining_or_past_secs = check_if_able_to_choose_seat(course=course, period=period)

    if access_type == Error.YOU_ARE_TOO_LATE:
        handle_error(Error.COURSE_ALREADY_BEGUN)
    if access_type == -1:
        handle_error(Error.SEAT_CHOOSING_NOT_AVAILABLE_YET,
                     remaining_secs=remaining_or_past_secs)
    if isinstance(access_type, Error):
        handle_error(access_type)
    get = get_json()
    seat_id = get('seat_id')
    seat = get_by_id_or_ERROR(Seat, seat_id, error=Error.SEAT_NOT_FOUND)
    stu_id = g.user.user_id
    if seat.modify({'students__' + str(period_num) + '__nin': [None, '']},
                   **{'students__' + str(period_num): '', 'late_secs__' + str(period_num): 0}):
        return success_reponse(seat_id=seat_id)
    handle_error(Error.SEAT_ALREADY_FREE_OR_TAKEN, seat_id=seat_id)


@main.route('/course/getMainCourse', methods=['GET', 'POST'])
def get_main_course():
    get = get_json()
    course = Course.objects(course_id=get('course_id')).first()
    if course:
        return make_response(jsonify(course.to_dict_all()), 200)
    abort(404)


@main.route('/course/getSubCourseDetails', methods=['POST'])
# @require_having_sub_course
@require_token
def get_sub_course():
    course = get_sub_course_pre()
    role = g.user.role
    return success_reponse(sub_course=course.to_dict_all(from_preview=True, for_teacher=False))


@main.route('/course/notification/getNotifications', methods=['POST'])
@require_having_sub_course
def get_notifications():
    course = get_sub_course_pre()
    print course.get_notifications_list()
    return success_reponse(notifications=course.get_notifications_list())


@main.route('/course/notification/postNotification', methods=['POST'])
# @require_is_teacher
@require_having_sub_course
def post_notification():
    course = get_sub_course_pre()
    get = get_json()
    content = get('content')
    on_top = get('on_top')
    title = get('title')
    by = g.user.name
    notification = Notification(title=title, created_on=datetime.datetime.now(), content=content, on_top=on_top, by=by,
                                unread_students=no_dereference_id_only(course.students))
    course.update(push__notifications=notification)

    try:
        course.save()
    except NotImplementedError:
        handle_error(Error.UNKNOWN_INTERNAL_ERROR)

    return success_reponse(ntfc_id=str(notification.ntfc_id))


@main.route('/course/notification/modifyNotification', methods=['POST'])
@require_is_teacher
@require_having_sub_course
def modify_notification():
    course = get_sub_course_pre()
    allowed = ['content', 'title', 'on_top']
    get = get_json()
    try:
        notification = course.notifications.get(ntfc_id=ObjectId(get('ntfc_id')))
    except:
        handle_error(Error.NOTIFICATION_NOT_FOUND)
    modify_from_request_or_422(instance=notification, allowed_fields=allowed,
                               exceptions=['ntfc_id', 'course_id', 'sub_id'])
    try:
        course.notifications.save()
    except:
        handle_error(Error.UNKNOWN_INTERNAL_ERROR)
    return success_reponse(ntfc_id=str(notification.ntfc_id))


@main.route('/course/notification/deleteNotification', methods=['POST'])
def delete_notification():
    course = get_sub_course_pre()
    get = get_json()
    ntfc_id = get('ntfc_id')
    course.update(pull__notifications__ntfc_id=ntfc_id)
    return success_reponse()


@main.route('/course/notification/markRead', methods=['POST'])
@require_token
def mark_read():
    get = get_json()
    combined_id = get('course_id') + '#' + get('sub_id')
    query = SubCourse.objects(pk=combined_id)
    query.filter(notifications__ntfc_id=ObjectId(get('ntfc_id'))).update(
        pull__notifications__S__unread_students=g.user.user_id)
    return success_reponse()


@main.route('/course/notification/markUnread', methods=['POST'])
@require_token
def mark_unread():
    get = get_json()
    combined_id = get('course_id') + '#' + get('sub_id')
    query = SubCourse.objects(pk=combined_id)
    query.filter(notifications__ntfc_id=ObjectId(get('ntfc_id'))).update(
        add_to_set__notifications__S__unread_students=g.user.user_id)
    return success_reponse()


@main.route('/course/notification/getUnreadNotifications', methods=['POST'])
@require_having_sub_course
def get_unread():
    course = g.sub_course
    return success_reponse(notifications=course.get_unread_notifications(student=g.user))


@main.route('/course/syllabus/getSyllabus', methods=['POST'])
@require_having_main_course
def get_syllabus():
    course = g.main_course
    return success_reponse(chapters=course.syllabus.to_dict())


@main.route('/course/syllabus/addChapters', methods=['POST'])
@require_having_main_course
def add_chapter():
    course = g.main_course
    get = get_json()
    chapters = get('chapters')
    r = course.syllabus.add_chapters(chapters_dict=chapters)
    if isinstance(r, Error):
        handle_error(r)
    return success_reponse()


@main.route('/course/syllabus/addSections', methods=['POST'])
@require_having_main_course
def add_section():
    course = g.main_course
    get = get_json()
    sections = get('sections')
    try:
        r = course.syllabus.add_sections(sections_dict=sections)
    except KeyError, key:
        handle_error(Error.FIELD_MISSING, field=key.message)
    if isinstance(r, Error):
        handle_error(r)
    return success_reponse()


@main.route('/course/timeAndRoom/getTimes', methods=['POST'])
def get_time_and_room():
    course = get_sub_course_pre()
    return success_reponse(times=course.get_times_and_rooms_dict())


@main.route('/course/registerTeacher', methods=['POST'])
def course_register_teacher():
    course = get_sub_course_pre()
    get = get_json()
    teacher_id = get('teacher_id')
    teacher = get_by_id_or_ERROR(Teacher, teacher_id)
    if not teacher:
        handle_error(Error.USER_NOT_FOUND)
    if not course:
        handle_error(Error.SUB_COURSE_NOT_FOUND)
    course.update(add_to_set__teachers=teacher)
    teacher.update(add_to_set__courses=course, add_to_set__main_course_ids=course.course_id)
    return success_reponse()


@main.route('/course/getAllStudents', methods=['POST'])
def get_all_students():
    course = get_sub_course_pre()
    return success_reponse(students=course.get_students_dict())
