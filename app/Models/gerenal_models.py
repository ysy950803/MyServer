# -*- coding: utf-8 -*-
from . import *

WEEK_NO = 1


class TeachDay:
    def __init__(self, day_no, week_no=WEEK_NO):
        if not isinstance(week_no, int) or not isinstance(day_no, int):
            raise TypeError
        self.week = week_no
        self.day = day_no

    @staticmethod
    def get_now_teach_day():
        return TeachDay(day_no=datetime.datetime.now().isoweekday())

    @staticmethod
    def is_course_on_day_and_get_period(course, day=None):
        if day is None:
            day = TeachDay.get_now_teach_day()
        for time in course.times:
            if day.week in time.weeks and day.day in time.days:
                period = Period.get_period(time.period)
                period.teach_day = day
                period.room_id = time.room_id
                return period
        return None


class Period:
    PERIOD_LIST = []

    def __init__(self, num, begin_at, end_at, teach_day=None, room_id=None):
        if not isinstance(num, int) or not isinstance(begin_at, (str, datetime.time)) or not isinstance(end_at, (
                str, datetime.time)):
            raise TypeError
        if num < 0:
            raise ValueError
        self.num = num
        if isinstance(begin_at, str):
            h, m, s = map(lambda x: int(x), begin_at.split(':'))
            self.begin_at = datetime.time(h, m, s)
        else:
            self.begin_at = begin_at
        if isinstance(end_at, str):
            h, m, s = map(lambda x: int(x), end_at.split(':'))
            self.end_at = datetime.time(h, m, s)
        else:
            self.end_at = end_at

        if self.begin_at >= self.end_at:
            raise ValueError
        if self.begin_at < datetime.time(12, 0, 0):
            self.is_am = True
        self.teach_day = teach_day
        self.room_id = room_id

    def is_on_going(self, at_time=datetime.datetime.now().time()):
        return self.begin_at <= at_time <= self.end_at

    def cmp_to_time(self, time):
        if time < self.begin_at:
            return 1
        if self.end_at < time:
            return -1
        return 0

    def get_remaining_seconds_before_beginning(self, time=None):
        if time is None:
            time = datetime.datetime.now().time()
        if time > self.end_at:
            return -1  # 已经结束
        if self.is_on_going(time):
            return 0  # 已经开始
        return (self.begin_at.hour - time.hour) * 3600 + (self.begin_at.minute - time.minute) * 60 + (
            self.begin_at.second - time.second)

    def get_remaining_seconds_before_ending(self, time=None):
        if time is None:
            time = datetime.datetime.now().time()
        if time > self.end_at:
            return -1  # 已经结束
        return (self.end_at.hour - time.hour) * 3600 + (self.end_at.minute - time.minute) * 60 + (
            self.end_at.second - time.second)

    def get_past_seconds(self, time=None):
        if time is None:
            time = datetime.datetime.now().time()
        if time < self.begin_at:
            return 0
        if time >= self.begin_at:
            if self.is_on_going(time):
                return (time.hour - self.begin_at.hour) * 3600 + (time.minute - self.begin_at.minute) * 60 + (
                    time.second - self.begin_at.second)
            return -1

    def get_previous_period(self):
        if self.num == 0:
            return self
        return Period.PERIOD_LIST[self.num - 1]

    def is_over(self, time=None):
        if time is None:
            time = datetime.datetime.now().time()
        return time > self.end_at

    @staticmethod
    def get_current_period_num(period_list=PERIOD_LIST, time=None):
        if time is None:
            time = datetime.datetime.now().time()
        result = None
        for period in period_list:
            cmp_result = period.cmp_to_time(time)
            if cmp_result == -1:
                continue
            if cmp_result == 0:
                return str(period.num)
            else:
                result = str(period.num - 1) + '.5'
                break
        if result is None:
            result = '0.5'
        return result

    @staticmethod
    def get_period(num):
        return Period.PERIOD_LIST[num]


zero = Period(0, '1:05:00', '08:00:00')
f = Period(1, '08:00:00', '09:35:00')
s = Period(2, '09:55:00', '11:30:00')
t = Period(3, '13:30:00', '15:05:00')
fo = Period(4, '15:20:00', '16:55:00')
fi = Period(5, '17:10:00', '18:45:00')
si = Period(6, '19:30:00', '23:05:00')
Period.PERIOD_LIST = [zero, f, s, t, fo, fi, si]


def can_choose_seat_at(at_time=datetime.datetime.now().time()):
    pass


class EachClassTime(EmbeddedDocument):
    num = IntField()
    begins_at = DateTimeField()
    ends_at = DateTimeField()


class TimeSchedule(Document):
    times = EmbeddedDocumentListField(EachClassTime)

    def get_current_period(self):
        pass


first = EachClassTime(num=1, begins_at=datetime.datetime.now(), ends_at=datetime.datetime.now())


class DClass(Document):
    class_id = StringField(primary_key=True)
    class_name = StringField(required=True)
    grade = IntField(required=True)
    students = ListField(DictField(), required=True, default=[])


class Major(Document):
    major_id = StringField(primary_key=True)
    major_name = StringField(required=True)
    eng_name = StringField(required=True)
    classes = ListField(DictField(), required=True, default=[])

    def to_dict(self, show_classes=False):
        json = {'major_id': self.major_id, 'major_name': self.name, 'eng_name': self.eng_name}
        if show_classes:
            json['classes'] = self.classes
        return json


class Department(Document):
    dept_id = StringField(primary_key=True)
    dept_name = StringField(required=True)
    eng_name = StringField(required=True)
    teachers = ListField(DictField(), required=True, default=[])

    def to_dict(self, show_teachers=False):
        json = {'dept_id': self.dept_id, 'dept_name': self.name, 'eng_name': self.eng_name}
        if show_teachers:
            json['teachers'] = self.teachers
        return json


class School(Document):
    school_id = StringField(primary_key=True)
    school_name = StringField(required=True)
    eng_name = StringField(required=True)
    departments = ListField(DictField(), required=True, default=DictField())
    majors = ListField(DictField(), required=True, default=DictField())
    courses = ListField(DictField(), required=True, default=DictField())

    def to_dict(self, show_departments=False, show_majors=False, show_courses=False):
        json = {'school_id': self.school_id, 'school_name': self.name, 'eng_name': self.eng_name}
        if show_departments:
            json['departments'] = self.departments
        if show_majors:
            json['majors'] = self.majors
        if show_courses:
            json['courses'] = self.courses
        return json


class Seat(Document):
    seat_id = StringField(primary_key=True)
    room_id = StringField(required=True)
    row = IntField(required=True)
    col = IntField(required=True)
    cur_stu = StringField(default="")
    #exists = BooleanField(required=True)
    late = IntField(default=0)
    students = DictField(default={})
    late_secs = DictField(default={})
    status = IntField(default=0)

    def to_dict(self, period, show_late_secs=False):
        period = str(period)
        json = {'seat_id': self.seat_id, 'row': self.row, 'col': self.col,
                'status': self.status}
        student_id = self.students.get(period)
        json['cur_stu'] = student_id or ''
        if show_late_secs:
            json['late_secs'] = self.late_secs.get(period) or 0
        return json

    def to_dict_all(self):
        return self.to_mongo()

    def to_dict_preview(self):
        return {'seat_id': self.seat_id, 'row': self.row, 'col': self.col, 'status': self.status}

    def parse_id(self):
        def to_str(integer):
            if integer < 10:
                return '00' + str(integer)
            if integer < 100:
                return '0' + str(integer)
            return str(integer)

        self.seat_id = self.room_id + ''.join(map(lambda x: to_str(x), [self.row, self.col]))


class Room(Document):
    room_id = StringField(primary_key=True)
    seats = ListField(ReferenceField(Seat))
    name = StringField(required=True)
    row = IntField(required=True)
    col = IntField(required=True)

    def get_seats_dict(self, period=0, show_late_secs=False, preview=False):
        assert (not (preview and show_late_secs))
        if preview:
            return map(lambda x: x.to_dict_preview(), self.seats)
        assert (period != 0)
        return map(lambda x: x.to_dict(period=period, show_late_secs=show_late_secs), self.seats)
