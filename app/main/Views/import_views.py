# -*- coding: utf-8 -*-
from . import *


@main.route('/test/subcourse', methods=['POST'])
def test_sub():
    get = get_json()
    course_id = get('course_id')
    sub_id = get('sub_id')
    combined_id = course_id + '#' + sub_id
    course = Course.objects(course_id=course_id).first()
    if not course:
        handle_error(Error.RESOURCE_NOT_FOUND)
    name = get('name')
    times = get('times')

    sub_course = SubCourse.objects(course_id=course_id, sub_id=sub_id).first()
    if sub_course:
        handle_error(Error.SUB_COURSE_ALREADY_EXISTS)
    sub_course = SubCourse(course_id=course_id, sub_id=sub_id, name=name, combined_id=combined_id, times=times)
    sub_course.save()
    course.update(add_to_set__sub_courses=sub_course, add_to_set__sub_course_ids=sub_course.sub_id)
    return success_reponse()


@main.route('/test/course', methods=['POST'])
def test_cousre():
    get = get_json()
    course_id = get('course_id')
    c = Course.objects(course_id=course_id).first()
    if c:
        handle_error(Error.MAIN_COURSE_ALREADY_EXISTS)
    instantiate_from_request_or_422(Course).save()
    return success_reponse()


@main.route('/test/seat', methods=['POST'])
def test_seat():
    get = get_json()

    room_id = get('room_id')
    room = get_by_id_or_ERROR(Room, room_id, error=Error.ROOM_NOT_FOUND)
    seat = instantiate_from_request_or_422(Seat, 'seat_id')
    seat.parse_id()
    try:
        seat.save()
    except NotUniqueError:
        handle_error(Error.SEAT_ALREADY_EXISTS)
    room.update(add_to_set__seats=seat)
    return success_reponse(seat_id=seat.seat_id)


@main.route('/test/course/knowledgePoint', methods=['POST'])
def test_knowledge_point():
    point = instantiate_from_request_or_422(KnowledgePoint)
    point.save()
    return success_reponse()


@main.route('/test_time')
def test_time():
    course = SubCourse.objects.first()
    return success_reponse(time=TeachDay.course_is_today(course))
