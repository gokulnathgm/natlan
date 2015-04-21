import os
basedir = os.path.abspath(os.path.dirname(__file__))


DATABASE = 'site.db'
DEBUG = True
DATABASE_PATH = os.path.join(basedir, DATABASE)
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH
SECRET_KEY = "this is some kind of secret"
IMAGE_FOLDER = 'static/files/images/'
DOC_FOLDER = 'static/files/docs'

MAIL_SERVER='smtp.gmail.com'
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''