from pymongo import MongoClient
from exceptions.StudentExistsException import StudentExistsException
from email_sender import send_email
import pickle
import os

client = MongoClient(os.environ['MONGODB_HOST_NAME'])
db = client[os.environ['MONGODB_DB_NAME']]
collection = db[os.environ['MONGODB_COLLECTION_NAME']]


def add_student_to_course(course, student):
    # serialization of objects
    student_binary = pickle.dumps(student)
    course_binary = pickle.dumps(course)

    if not student in course.students:
        collection.update_one({'_id': course.unique_id},
                              {'$set':
                                   {'course': course_binary},
                               '$push':
                                   {'students': student_binary},
                               },
                              upsert=True)
        course.add_student(student)
        send_email(student, course, 'verification')
    else:
        raise StudentExistsException()


def remove_course(course):
    collection.delete_one({'_id': course.unique_id})


def get_courses():
    documents = list(collection.find({}))
    courses = []
    for course_binary in documents:
        # deserializes objects
        course = pickle.loads(course_binary['course'])

        for student_binary in course_binary['students']:
            student = pickle.loads(student_binary)
            course.add_student(student)
        courses.append(course)
    return courses


def get_number_of_courses():
    return collection.estimated_document_count()
