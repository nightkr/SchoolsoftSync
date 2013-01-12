import requests
from bs4 import BeautifulSoup, NavigableString

from . import calendartools

import itertools
import re
import datetime


_login_page_re = r'https://sms(\d+).schoolsoft.se/%s/jsp/student/../../html/redirect_student.htm'
_sched_print_weeknum_strip_re = re.compile(r'(.+?)&term=\d+')


class User(object):
    def __init__(self, school, username, password):
        self.school = school
        self.username = username
        self.password = password
        
        self.cookies = {}
        
        self._login_page_re = re.compile(_login_page_re % school)
    
    def _try_get(self, url, attempts=0):
        r = requests.get(url, cookies=self.cookies)
        
        login_page_match = self._login_page_re.match(r.url)
        if login_page_match:
            server_n, = login_page_match.groups()
            if attempts < 1:
                loginr = requests.post("https://sms%s.schoolsoft.se/%s/jsp/Login.jsp" % (server_n, self.school), data={
                    'action': 'login',
                    'usertype': 1, # "Elev"
                    'ssusername': self.username,
                    'sspassword': self.password,
                }, cookies=self.cookies, allow_redirects=False)
                self.cookies = loginr.cookies
                return self._try_get(url, attempts+1)
            else:
                raise AuthFailure("Unable to log in, verify login info")
        else:
            return r

    def _parse_schedule(self, sched, weekno):
        days = [0] * 5
        events = [[]] * 5

        for row in sched.table.contents[1:]:
            if not isinstance(row, NavigableString):
                for day in row:#.find_all(attrs={'class':lambda x: ((x == ' schedulecell') or (x == 'printLight schedulecell'))}):
                    _class = day.attrs.get('class')
                    if _class == ['', 'schedulecell'] or _class == ['printLight', 'schedulecell']:
                        i = days.index(0)
                        days[i] = int(day.attrs['rowspan'])

                        if _class[0] == '':
                            eventtable = day.table

                            course_code, start_time, = eventtable.tr
                            location, end_time, = course_code.parent.next_sibling
                            course_readable, = location.parent.next_sibling
                            teacher, = course_readable.parent.next_sibling

                            event = {
                                'course_code': course_code.text.strip(),
                                'course_readable': course_readable.text.strip(),
                                'teacher': teacher.text.strip(),
                                'location': location.text.strip() or None,
                                'start_time': datetime.datetime.strptime(start_time.text, "%H:%M").time(),
                                'end_time': datetime.datetime.strptime(end_time.text[1:], "%H:%M").time(),
                            }
                            events[i].append(event)

                days = [max(0, i - 1) for i in days]

        schedule = [(calendartools.iso_to_gregorian(datetime.date.today().year, weekno, day), day_events) for (day, day_events) in zip(itertools.count(0), events)]
        return schedule

    def _student_weeknum_schedule(self, print_link_base, weeknum):
        schedr = self._try_get('https://sms.schoolsoft.se/%s/jsp/student/%s&term=%i' % (self.school, print_link_base, weeknum))
        sched = BeautifulSoup(schedr.text)
        
        return self._parse_schedule(sched, weeknum)
    
    def personal_student_schedule(self, weeknums=None):
        if weeknums == None:
            this_week = datetime.date.today().isocalendar()[1]
            weeknums = [this_week, this_week + 1]

        parentr = self._try_get('https://sms.schoolsoft.se/%s/jsp/student/right_student_schedule.jsp' % self.school)
        parent = BeautifulSoup(parentr.text)
        print_btn = parent.find(src="../../images/icon/printer.png").parent
        print_link = print_btn['onclick']
        print_link = print_link[len("popupWindow('"):-len("')")]
        
        print_link_base, = _sched_print_weeknum_strip_re.match(print_link).groups()
        return [self._student_weeknum_schedule(print_link_base, weeknum) for weeknum in weeknums]


class AuthFailure(Exception):
    pass