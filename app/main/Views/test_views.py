# -*- coding: utf-8 -*-
from . import *


@main.route('/course/question/postQuestion', methods=['POST'])
def post_question():
    course = get_main_course_pre()
    get = get_json()
    # identifier=get('identifier')
    try:
        point = KnowledgePoint.objects(point_id=get('point_id')).first()
    except ValidationError:
        handle_error(Error.RESOURCE_NOT_FOUND)
    if not point:
        handle_error(Error.RESOURCE_NOT_FOUND)
    answers = get('answers')
    choices = get('choices')
    question = instantiate_from_request_or_422(Question, knowledge_point=point, answers=answers, choices=choices)
    question.save()
    point.update(add_to_set__questions=question)
    return success_reponse(quest_id=str(question.quest_id))


@main.route('/course/question/modifyQuestion', methods=['POST'])
def modify_question():
    get = get_json()
    quest_id = get('quest_id')
    question = Question.objects(quest_id=quest_id).first()
    point_id = get('point_id')
    try:
        point = KnowledgePoint.objects(point_id=get('point_id')).first()
    except ValidationError:
        handle_error(Error.RESOURCE_NOT_FOUND)
    if not question:
        handle_error(Error.RESOURCE_NOT_FOUND)
    modify_from_request_or_422(question, knowledge_point=point)
    question.save()
    return success_reponse()


@main.route('/course/question/deleteQuestion', methods=['POST'])
def delete_question():
    get = get_json()
    quest_id = get('quest_id')
    # identifier = get('identifier')
    question = Question.objects(quest_id=quest_id).first()
    if not question:
        return success_reponse()
    question.delete()
    return success_reponse()


@main.route('/course/question/getAllQuestions', methods=['POST'])
@require_having_main_course
@require_is_teacher
def get_all_questions():
    get = get_json()
    course_id = get('course_id')
    page = get('page')
    per_page = get('per_page', allow_none=True)
    course = get_by_id_or_ERROR(Course, course_id)
    questions = course.get_questions_dict_paginating(page=page, per_page=PER_PAGE)
    return success_reponse(questions=questions)


@main.route('/course/question/getQuestion', methods=['POST'])
@require_having_main_course
@require_is_teacher
def get_question():
    get = get_json()
    question = get_by_id_or_ERROR(Question, get('quest_id'))
    return success_reponse(question=question.to_dict_all())


@main.route('/course/question/getQuestionsWithList', methods=['POST'])
def get_questions():
    get = get_json()
    question_list = get('questions')
    questions = []

    def get_question(quest_id):
        try:
            q = Question.objects(quest_id=quest_id).first()
        except ValidationError:
            handle_error(Error.RESOURCE_NOT_FOUND)
        if not q:
            handle_error(Error.RESOURCE_NOT_FOUND)
        questions.append(q.to_dict_all())

    map(get_question, question_list)
    return success_reponse(questions=questions)


@main.route('/course/test/postTest', methods=['POST'])
@require_token
def post_test():
    course = get_course_pre()
    get = get_json()
    question_ids = get('questions')
    questions = []
    course_id = get('course_id')
    sub_id = get('sub_id')
    combined_id = course_id + '#' + sub_id
    by = g.user.user_id
    map(lambda quest_id: questions.append(get_by_id_or_ERROR(Question, quest_id)), question_ids)
    new_test = instantiate_from_request_or_422(Test, questions=questions, combined_id=combined_id)
    new_test.save()
    course.update(add_to_set__tests=new_test)
    return success_reponse(test_id=str(new_test.test_id))


@main.route('/course/test/getAllTests', methods=['POST'])
@require_having_sub_course
def get_all_tests():
    course = get_course_pre()
    get = get_json()
    role = get('role')
    page = get('page')
    if role == 2:  # 学生用
        unfinished_only = get('finished')
        tests = course.get_all_tests_dict_paginating(page=page, per_page=PER_PAGE, finished=unfinished_only,
                                                     student_id=g.user.user_id)
        return success_reponse(page=page, tests=tests)
    elif role == 1:  # 教师用
        tests = course.get_all_tests_dict_paginating(page=page, per_page=PER_PAGE)
        return success_reponse(page=page, tests=tests)


@main.route('/course/test/getTestDetails', methods=['POST'])
@require_having_sub_course
def get_test():
    get = get_json()
    test_id = get('test_id')
    test = get_by_id_or_ERROR(Test, test_id)
    return success_reponse(test=test.to_dict_all())


@main.route('/course/test/getTestQuestions', methods=['POST'])
def get_test_questions():
    get = get_json()
    test_id = get('test_id')
    test = get_by_id_or_ERROR(Test, test_id)
    return success_reponse(questions=test.get_random_questions())


