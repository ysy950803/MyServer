# -*- coding: utf-8 -*-
from . import *
import random
from ..main.errors import *
from .user_models import Student


class TimeAndRoom(EmbeddedDocument):
    room_name = StringField(required=True)
    room_id = StringField(required=True)
    days = ListField(IntField(), required=True)
    period = IntField(required=True)
    weeks = ListField(IntField(), required=True)

    def to_dict(self):
        return {'room_name': self.room_name, 'room_id': self.room_id, 'days': self.days, 'period':
            self.period, 'weeks': self.weeks}


# 知识点
class KnowledgePoint(Document):
    course_id = StringField(required=True)
    chapter = IntField(required=True)
    point_id = ObjectIdField(default=lambda: ObjectId(), primary_key=True)
    content = StringField(required=True)
    num = IntField(required=True)
    level = IntField(required=True)
    questions = ListField(ReferenceField('Question'))

    def to_dict(self):
        return {'num': self.num, 'chapter': self.chapter, 'content': self.content, 'point_id': str(self.point_id),
                'level': self.level}


# 课程通知
class Notification(EmbeddedDocument):
    ntfc_id = ObjectIdField(required=True, default=lambda: ObjectId())
    created_on = DateTimeField(default=lambda: datetime.datetime.now())
    content = StringField(required=True)
    title = StringField(required=True)
    on_top = BooleanField(required=True)
    by = StringField(required=True)
    unread_students = ListField(StringField(), required=True)

    def to_dict(self):
        return {'ntfc_id': str(self.ntfc_id), 'created_on': time_to_string(self.created_on), 'content': self.content,
                'on_top':
                    self.on_top, 'by': self.by, 'title': self.title}


class Question(Document):
    course_id = StringField(required=True)
    quest_id = ObjectIdField(default=lambda: ObjectId(), primary_key=True)
    created_on = DateTimeField(default=lambda: datetime.datetime.now())
    last_modified = DateTimeField(default=lambda: datetime.datetime.now())
    type = IntField(required=True)
    choices = ListField(StringField(), required=True)
    content = StringField(required=True)
    difficulty = IntField(required=True)
    answers = ListField(IntField(), required=True)
    detailed_answer = StringField(required=True)
    knowledge_point = ReferenceField('KnowledgePoint', reverse_delete_rule=1, required=True)
    point_id = StringField()
    by = StringField()
    hint = StringField(required=True)

    def to_dict_student_test(self):
        return {'quest_id': str(self.quest_id), 'type': self.type, 'choices': self.choices, 'content': self.content,
                'difficulty': self.difficulty, 'answers': self.answers, 'detailed_answer': self.detailed_answer,
                'point_id': str(self.knowledge_point.point_id)}

    def to_dict_all(self):
        temp_dict = self.to_dict_student_test()
        temp_dict['created_on'] = self.created_on
        # temp_dict['last_modified'] = self.last_modified
        temp_dict['by'] = self.by
        return temp_dict

    def to_dict_preview(self):
        return {'quest_id': self.quest_id, 'content': self.content, 'type': self.type, 'point_id': self.point_id}


class TestQuestionResult(EmbeddedDocument):
    question_id = StringField(required=True)
    is_correct = BooleanField()
    choice = IntField()
    content = StringField()


class TestResult(Document):
    test_id = StringField(required=True)
    student_id = StringField(required=True)
    # student_ref = ReferenceField('Student')
    # results = EmbeddedDocumentListField()


class TestStatistic(EmbeddedDocument):
    pass


class RandomQuestionPreference(EmbeddedDocument):
    knowledge_point = ReferenceField(KnowledgePoint, required=True)
    num = IntField(required=True)


class Test(Document):
    course_id = StringField(required=True)
    sub_id = StringField(required=True)
    test_id = ObjectIdField(default=lambda: ObjectId(), primary_key=True)
    combined_id = StringField(required=True)
    created_on = DateTimeField(default=lambda: datetime.datetime.now(), required=True)
    begins_on = DateTimeField(default=lambda: datetime.datetime.now(), required=True)
    expires_on = DateTimeField()
    questions = ListField(ReferenceField(Question, reverse_delete_rule=PULL), required=True)
    question_ids = ListField(StringField())
    done_students = ListField(ReferenceField('Student'))
    results = ListField(ReferenceField(TestResult, reverse_delete_rule=PULL))
    statistic = EmbeddedDocumentField(TestStatistic)
    message = StringField()
    time_limit = IntField(required=True)
    has_hint = ListField(BooleanField())
    random_type = IntField(required=True, default=0)
    blacklist = ListField(StringField())
    black_info = StringField()
    random_preferences = EmbeddedDocumentListField(RandomQuestionPreference)
    by = StringField(required=True)

    def to_dict_student_take(self):
        json = dict()
        json['test_id'] = str(self.test_id)
        json['begins_on'] = time_to_string(self.begins_on)
        json['expires_on'] = time_to_string(self.begins_on)
        json['message'] = self.message
        json['has_hint'] = self.has_hint
        json['blacklist'] = self.blacklist
        json['done_students'] = self.done_students
        return json

    def to_dict_all(self):
        json = self.to_dict_student_take()
        json['created_on'] = self.created_on
        return json

    def to_dict_preview(self):
        json = dict()
        json['test_id'] = str(self.test_id)
        json['begins_on'] = time_to_string(self.begins_on)
        json['expires_on'] = time_to_string(self.begins_on)
        json['message'] = self.message
        return json

    def get_questions_dict(self, question_list=None):
        questions = []
        if question_list == None:
            map(lambda x: questions.append(x.to_dict_student_test()), self.questions)
        else:
            map(lambda x: questions.append(x.to_dict_student_test()), question_list)
        return questions

    def get_random_questions(self):
        if self.random_type == 0:
            return self.get_questions_dict()
        elif self.random_type == 1:
            new_list = list(self.questions)
            random.shuffle(new_list)
            return self.get_questions_dict(new_list)
        elif self.random_type == 2:
            if not self.random_preferences:
                return Error.RANDOM_TEST_NOT_SET
            new_list = []

            def choose_question(preference):
                raw_list = random.sample(preference.knowledge_point.questions, preference.num)
                temp_list = []
                map(lambda x: temp_list.append(x.to_dict_student_test()), raw_list)
                new_list.extend(temp_list)

            map(choose_question, self.random_preferences)
            random.shuffle(new_list)
            return new_list


class SubCourseSetting(EmbeddedDocument):
    allow_late = IntField(default=0)


# 讲台
class SubCourse(Document):
    name = StringField(required=True)
    combined_id = StringField(primary_key=True)
    course_id = StringField(required=True)
    sub_id = StringField(required=True)
    teachers = ListField(ReferenceField('Teacher'), required=True)
    students = ListField(ReferenceField('Student'), required=True)
    notifications = EmbeddedDocumentListField(Notification)
    times = EmbeddedDocumentListField(TimeAndRoom)
    tests = ListField(ReferenceField('Test', reverse_delete_rule=PULL))
    settings = EmbeddedDocumentField(SubCourseSetting, required=True, default=SubCourseSetting())
    classes = ListField(StringField())

    def to_dict_all(self, from_preview=False, for_teacher=False):
        extra = {'students': self.get_students_dict(for_teacher=for_teacher), 'ntfcs': self.get_notifications_list()}
        if not from_preview:
            extra.update(self.to_dict_brief())
        return extra

    def to_dict_brief(self):
        teachers = []
        map(lambda x: teachers.append(x.name), self.teachers)
        return {'course_id': self.course_id, 'sub_id': self.sub_id, 'teachers': teachers, 'course_name': self.name,
                'times': self.get_times_and_rooms_dict()}

    def to_dict_brief_on_login_student(self, student):
        json = self.to_dict_brief()
        json['unread_ntfcs'] = self.get_unread_notifications(student)
        json['untaken_tests'] = self.get_untaken_tests(student)
        return json

    def get_students_dict(self, for_teacher=False):
        if for_teacher:
            return map(lambda x: x.to_dict_brief_for_teacher(), self.students)
        # return map(lambda x: x.to_dict_brief(), self.students)
        return no_dereference_id_only(self.students)

    def get_teachers_dict(self):
        teachers = []
        map(lambda x: teachers.append(x.to_dict_brief()), self.teachers)
        return teachers

    def get_times_and_rooms_dict(self):
        times = []
        map(lambda x: times.append(x.to_dict()), self.times)
        return times

    # 返回课程通知列表
    def get_notifications_list(self):
        normal_notifications = []
        top_notifications = []
        for notification in self.notifications:
            if notification.on_top:
                top_notifications.append(notification.to_dict())
            else:
                normal_notifications.append(notification.to_dict())
        normal_notifications.extend(top_notifications)
        normal_notifications.reverse()
        return normal_notifications

    def get_all_tests_dict_paginating(self, page, per_page, finished=False, student_id=None):
        offset = (page - 1) * per_page
        test_list = []
        if finished:
            test_list = Test.objects(combined_id=self.combined_id, done_students__nin=[student_id]).order_by(
                '-begins_on').skip(offset).limit(per_page)
        elif not finished and student_id is not None:
            test_list = Test.objects(combined_id=self.combined_id, done_students__in=[student_id]).order_by(
                '-begins_on').skip(offset).limit(per_page)
        else:
            test_list = Test.objects(combined_id=self.combined_id).order_by(
                '-begins_on').skip(offset).limit(per_page)
        tests = []
        map(lambda x: tests.append(x.to_dict_student_take()), test_list)
        return tests

    def get_unread_notifications(self, student):
        notifications = []
        for notification in self.notifications:
            if student.user_id in notification.unread_students:
                notifications.append(notification.to_dict())
        notifications.reverse()
        return notifications

    def get_untaken_tests(self, student):
        tests = []
        for test in no_dereference_id_only(self.tests):
            if test not in no_dereference_id_only(student.done_tests):
                tests.append(str(test))
        return tests


# 课程
class Course(Document):
    course_id = StringField(primary_key=True)
    name = StringField(required=True)
    department = StringField()
    sub_course_ids = ListField(StringField())
    sub_courses = ListField(ReferenceField(SubCourse, reverse_delete_rule=PULL))
    course_type = IntField()
    points = ListField(ReferenceField(KnowledgePoint, reverse_delete_rule=PULL))
    questions = ListField(ReferenceField(Question, reverse_delete_rule=PULL))

    def to_dict(self):
        subs = []
        map(lambda x: subs.append(x.to_dict_brief()), self.sub_courses)
        return {'course_id': self.course_id, 'sub_ids': self.sub_course_ids, 'subs': subs, 'type': self.course_type, \
                'knowledge_points': self.get_knowledge_points_dict(), 'course_name': self.name}

    def to_dict_brief(self):
        subs = []
        map(lambda x: subs.append(x.to_dict_brief()), self.sub_courses)
        return {'course_id': self.course_id, 'course_name': self.name, 'course_type': self.course_type, 'subs': subs}

    def get_knowledge_points_dict(self):
        points = []
        map(lambda x: points.append(x.to_dict_all()), self.points)
        return points

    def get_questions_dict_paginating(self, page, per_page):
        offset = (page - 1) * per_page
        questions = Question.objects(course_id=self.course_id).skip(offset).limit(per_page)
        question_dict = []
        map(lambda x: question_dict.append(x.to_dict_all()), questions)
        return question_dict


KnowledgePoint.register_delete_rule(Question, 'point_id', NULLIFY)
Question.register_delete_rule(KnowledgePoint, 'questions', PULL)
