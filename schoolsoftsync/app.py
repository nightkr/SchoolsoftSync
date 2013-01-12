from flask import Flask, request, Response, render_template, flash, url_for
import icalendar
import pytz

from . import schoolsoft, forms, models

import datetime
import os


app = Flask(__name__)
flask_config = os.environ.get('FLASK_CONFIG', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev_settings.py'))
app.config.from_pyfile(flask_config)
models.db.init_app(app)


def ss_event_to_ical_event(day, event, tz):
    start_time = datetime.datetime.combine(day, event['start_time']).replace(tzinfo=tz)
    end_time = datetime.datetime.combine(day, event['end_time']).replace(tzinfo=tz)

    ical = icalendar.Event()
    ical.add('summary', "%s: %s with %s" % (event['course_code'], event['course_readable'], event['teacher']))
    ical.add('organizer;cn', event['teacher'])
    ical.add('dtstart', start_time)
    ical.add('dtend', end_time)
    ical['uid'] = "%s/%s" % (event['course_code'], start_time)

    if event['location']:
        ical.add('location', event['location'])

    return ical


def ss_day_to_ical_events(day, tz):
    day, events = day
    return [ss_event_to_ical_event(day, event, tz) for event in events]


def ss_cal_to_ical(weeks, tz):
    cal = icalendar.Calendar()
    cal.add('version', '2.0')

    for week in weeks:
        for day in week:
            for event in ss_day_to_ical_events(day, tz):
                cal.add_component(event)

    return cal


http_auth_fail = Response('Authentication information required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
db_auth_fail = Response('', 403)


def serialize(auth_fail, tz_region, tz, school, username, password):
    try:
        tz = pytz.timezone('%s/%s' % (tz_region, tz))

        user = schoolsoft.User(school, username, password)
        schedule = user.personal_student_schedule()

        return ss_cal_to_ical(schedule, tz).to_ical()
    except schoolsoft.AuthFailure:
        return auth_fail


@app.route("/ical/<tz_region>/<tz>/<school>")
def http_pass(tz_region, tz, school):
    auth = request.authorization
    if not auth:
        return http_auth_fail

    return serialize(http_auth_fail, tz_region, tz, school, auth.username, auth.password)


@app.route("/ical_stored/<tz_region>/<tz>/<school>/<username>/<hash>")
def db_pass(tz_region, tz, school, username, hash):
    cred = models.StoredCredential.query.filter_by(school=school, username=username).first()
    if not cred:
        return db_auth_fail
    try:
        password = cred.decrypt_password(hash.decode("hex"))
    except TypeError:
        return db_auth_fail
    return serialize(db_auth_fail, tz_region, tz, school, username, password)


@app.route("/", methods=["GET", "POST"])
def index():
    signup_form = forms.SignupForm(csrf_enabled=False)

    if signup_form.validate_on_submit():
        cred = signup_form.find_stored_credential()
        if cred and cred.decrypt_password(cred.get_password_crypto_key(signup_form.old_password.data)) != signup_form.old_password.data:
            flash("The old password didn't match, please enter your old password too")
        else:
            if not cred:
                cred = models.StoredCredential()
                cred.school = signup_form.school.data
                cred.username = signup_form.username.data
                models.db.session.add(cred)
            key, cred.encrypted_password = cred.encrypt_password(signup_form.password.data)
            models.db.session.commit()

            try:
                ss_user = schoolsoft.User(cred.school, cred.username, signup_form.password.data)
                ss_user._try_get("https://sms.schoolsoft.se/%s/" % cred.school)
                verified = True
            except Exception:
                flash("The credentials could not be verified with SchoolSoft")
                verified = False
                raise

            if verified:
                addr = url_for('db_pass', _external=True, tz_region='Europe', tz='Stockholm', school=cred.school, username=cred.username, hash=key.encode("hex"))
                flash("Signed up successfully, you can now subscribe to your schoolsoft schedule in your calendar by entering the address %s" % addr)

    return render_template('index.html', signup_form=signup_form)
