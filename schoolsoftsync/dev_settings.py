import os

SQLALCHEMY_DATABASE_URI = os.environ.get('HEROKU_POSTGRESQL_COPPER_URL', 'postgresqlD://schoolsoftsync:sss@localhost/schoolsoftsync')
SECRET_KEY='Hey, there!'  # Okay, since we don't store any secret state