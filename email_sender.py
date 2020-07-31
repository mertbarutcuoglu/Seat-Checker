import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

server = smtplib.SMTP(host='smtp.mailgun.org', port=587)
server.starttls()
from_email = os.environ['EMAIL_ADDRESS']
server.login(from_email, os.environ['EMAIL_PASSWORD'])


def get_custom_email(student, course, template):
    if template == 'verification':
        template_name = 'verification_template.txt'
    if template == 'notification':
        template_name = 'notification_template.txt'

    with open(f'email templates/{template_name}', 'r', encoding='utf-8') as template_file:
        email_template = Template(template_file.read())
        customized_email = email_template.substitute(STUDENT_NAME=student.name, COURSE_NAME=course.full_course_name)
        return customized_email


def send_email(student, course, purpose):
    body = get_custom_email(student, course, purpose)
    message = MIMEMultipart()

    if purpose == 'verification':
        subject = 'UBC Course Analyzer Verification'
    if purpose == 'notification':
        subject = f'A spot opened in {course.full_course_name}'

    message['From'] = from_email
    message['To'] = student.email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    server.send_message(message)