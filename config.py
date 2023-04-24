import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '1iqnFcVDN1y61Eza4lD1z2tgAZ3RF9gy'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Provisorisch, für Test mit flask shell
    if os.environ.get('SERVER_TYPE') != 'gunicorn':
        SERVER_NAME = 'localhost:5000'
    # SERVER_NAME kann später wieder entfernt werden

    POSTS_PER_PAGE = 5
    USERS_PER_PAGE = 10

    ADMIN = ["admin@lab2.ifalabs.org"]