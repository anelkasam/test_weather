from flask import render_template

from app import app


@app.route('/')
def hello_world():
    user = {'name': 'Elena'}
    return render_template('index.html',
                           city='Kyiv', user=user)
