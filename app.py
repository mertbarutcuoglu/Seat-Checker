import os

from flask import Flask, request, jsonify
from models.Course import Course
from models.Student import Student
from database import add_student_to_course, get_courses, get_number_of_courses, remove_course
from apscheduler.schedulers.background import BackgroundScheduler
from seat_checker import is_course_available
from email_sender import send_email
from exceptions.StudentExistsException import StudentExistsException
from requests.exceptions import RequestException
from socket import gaierror
import smtplib
import logging
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app, resources={r"/add/*": {"origins": "ubccourseanalyzer.com"}})

courses = []
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


@app.route('/add', methods=['POST'])
def add_student():
    global courses

    course_name = request.json['courseName']
    course_number = request.json['courseNumber']
    course_section = request.json['courseSection']

    new_course = Course(course_name, course_number, course_section)

    course_status = is_course_available(new_course) # checks if course is already available or if it is on SSC
    if course_status != False:
        if course_status == True:
            return jsonify({'response': 'Course is already available!'}), 400
        elif course_status == 'Course does not exist!':
            return jsonify({'response': course_status}), 400

    student_name = request.json['name']
    student_surname = request.json['surname']
    student_email = request.json['email']

    student = Student(student_name, student_surname, student_email)

    # gets the course from courses if the course exists, otherwise returns None
    existing_course = next((course for course in courses if course == new_course), None)
    try:
        if existing_course is not None:
            add_student_to_course(existing_course, student)
        else:
            num_courses_in_db = get_number_of_courses()

            # Checks if the db and list is synchronized
            if len(courses) == num_courses_in_db:
                courses.append(new_course)
                add_student_to_course(new_course, student)
            else:
                courses = get_courses()
                existing_course = next((course for course in courses if course == new_course), None)
                if existing_course is not None:
                    add_student_to_course(existing_course, student)
                else:
                    courses.append(new_course)
                    add_student_to_course(new_course, student)

    except StudentExistsException:
        return jsonify({'response': 'A student with this email address exists.'}), 400
    except Exception as e:
        logging.error('Registration error', exc_info=True)
        return jsonify({'response': 'An error occurred while registration. Please try again.'}), 500

    return jsonify({'response': 'Success.'}), 200

def check_spots():
    if courses:
        for course in courses:
            try:
                if is_course_available(course):
                    for student in course.students:
                        send_email(student, course, 'notification')
                    remove_course(course)
                    courses.remove(course)
            except RequestException:
                logging.error('Error when connecting to SSC', exc_info=True)
            except (gaierror, ConnectionRefusedError):
                logging.error('Failed to connect to the server. Bad connection settings?', exc_info=True)
            except smtplib.SMTPServerDisconnected:
                logging.error('Failed to connect to the server.', exc_info=True)
            except smtplib.SMTPException:
                logging.error('SMTP error', exc_info=True)
            except Exception as e:
                logging.error('Error occurred while checking courses', exc_info=True)

scheduler = BackgroundScheduler()
job = scheduler.add_job(check_spots, 'interval', minutes=5)
scheduler.start()

if __name__ == '__main__':
    app.run()
