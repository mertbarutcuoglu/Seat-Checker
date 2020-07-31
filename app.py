import os
import sys

from flask import Flask, request, render_template
from flask_wtf import CSRFProtect

from forms.AddUserForm import AddUserForm
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
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

cors = CORS(app, resources={r"/": {"origins": "https://seatchecker.ubccourseanalyzer.com"}})
csrf = CSRFProtect(app)

courses = []

# Logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

app.logger.addHandler(ch)


@app.route('/', methods=['GET', 'POST'])
def home():
    form = AddUserForm()
    if form.validate_on_submit():
        results = request.form

        global courses

        course_name = results['subject']
        course_number = results['course_no']
        course_section = results['course_section']

        new_course = Course(course_name, course_number, course_section)

        course_status = is_course_available(new_course)  # checks if course is already available or if it is on SSC
        if course_status != False:
            if course_status == True:
                return render_template('error.html', message='Course is already available!')
            elif course_status == 'Course does not exist!':
                return render_template('error.html', message=course_status)

        student_name = results['name']
        student_surname = results['surname']
        student_email = results['email']

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
            return render_template('error.html', message='A student with this email address exists.')
        except Exception as e:
            logging.error('Registration error', exc_info=True)
            return render_template('error.html', message='An error occurred during registration. Please try again.')
        return render_template('result.html')

    return render_template('seat_checker.html', form=form)


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
