from flask.ext.wtf import Form, TextField, PasswordField, Required
from . import models


class SignupForm(Form):
    school = TextField(description="https://sms.schoolsoft.se/THISTHINGRIGHTHERE/", validators=[Required()])
    username = TextField(validators=[Required()])
    password = PasswordField(validators=[Required()])

    def find_stored_credential(self):
        return models.StoredCredential.query.filter_by(school=self.school.data, username=self.username.data).first()
