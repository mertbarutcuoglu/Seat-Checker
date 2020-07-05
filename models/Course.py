import hashlib

from bson.objectid import ObjectId

class Course:
    base_url = 'https://courses.students.ubc.ca/cs/courseschedule?sesscd='

    def __init__(self, course_name, course_number, course_section):
        self.course_name = course_name
        self.course_number = course_number
        self.course_section = course_section
        self.full_course_name = ' '.join([course_name, course_number, course_section])
        self.students = set()
        self.course_url = self.base_url + f'W&pname=subjarea&tname=subj-section&course={course_number}'
        self.course_url += f'&sessyr=2020&section={course_section}&dept={course_name}'

        self.unique_id = hashlib.md5(self.course_url.encode('utf-8')).hexdigest()

    def add_student(self, student):
        self.students.add(student)

    def remove_student(self, student):
        self.students.remove(student)

    def __eq__(self, other):
        if not isinstance(other, Course):
            return NotImplemented

        return self.course_url == other.course_url

    def __hash__(self):
        return hash(self.course_url)
