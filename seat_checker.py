from bs4 import BeautifulSoup
import requests


def is_course_available(course):
    try:
        page = requests.get(course.course_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        seats_table = soup.find_all('table')[3]
        seats_remaining = list(seats_table.children)[3].find('strong').text

        if seats_remaining != '0':
            return True
        else:
            return False
    except IndexError as e:
        return 'Course does not exist!'
