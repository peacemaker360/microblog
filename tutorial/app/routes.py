# app/routes.py
from flask import render_template
from app import app
@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Fabian'}
    posts = [
        {
        'author': {'username': 'Paul'},
        'body': 'Schöner Abend hier in Zürich!'
        },
        {
        'author': {'username': 'Susanne'},
        'body': 'Der Unterricht war heute mal gut!'
        }
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)