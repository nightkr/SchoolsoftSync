SCHOOL = "nti"
USERNAME = "tekl"
PASSWORD = "FHXy8L:;ye+wtKlwy]S*"
#TIMEZONE = "Europe/Stockholm"

from schoolsoftsync import schoolsoft

user = schoolsoft.User(SCHOOL, USERNAME, PASSWORD)
print user.personal_student_schedule()[0][0]
