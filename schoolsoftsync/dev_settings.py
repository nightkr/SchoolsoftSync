import os

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://schoolsoftsync:sss@localhost/schoolsoftsync')
SECRET_KEY='Hey, there!'  # Okay, since we don't store any secret state