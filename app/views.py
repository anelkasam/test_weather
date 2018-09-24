import json
import requests

from datetime import datetime
from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm, CitySearchForm
from app.models import User, City, Forecast


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    search_form = CitySearchForm()
    context = {'form': search_form}
    if search_form.validate_on_submit():
        cities = City.query.filter_by(name=search_form.search.data)
        if not cities:
            flash(f'There no city {search_form.search.data} into database.')
            return redirect('index')
        context['cities'] = cities

    return render_template('index.html', context=context)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/list_cities')
def list_cities():
    cities = City.query.all()
    if not cities:
        with open('city.list.json', 'r') as f:
            city_data = json.load(f)

        for data in city_data:
            city = City(id=data['id'], name=data['name'], country=data['country'],
                        lat=data['coord']['lat'], lon=data['coord']['lon'])
            db.session.add(city)
        db.session.commit()
        flash('Congratulations, cities list saved into DB!')
    flash('The cities is already in the DB!')
    return redirect('index')


@app.route('/weather/<city_id>')
def weather(city_id):
    historic_url = f'http://history.openweathermap.org/data/2.5/history/city?' \
                   f'id={id}&type=hour&start={start}&end={end}&appid={appid}'
    forecast_url = f'api.openweathermap.org/data/2.5/forecast?' \
                   f'id={city_id}&mode=json&appid={appid}'
    city = City.query.get(city_id)
    context = {'city': city}
    return render_template('weather.html', context=context)


def get_data_from_openweathermap(city_id):
    """
    Get data from the openweathermap.org for the city for the last 2 weeks and forecast for the next 5 days.
    """
    delta = 1209600  # 2 weeks
    historic_url = f'http://history.openweathermap.org/data/2.5/history/city?' \
                   f'id={city_id}&type=hour&start={datetime.utcnow() - delta}&end={datetime.utcnow()}' \
                   f'&appid={app.config["OPENWEATHERMAP_API_KEY"]}'
    forecast_url = f'api.openweathermap.org/data/2.5/forecast?' \
                   f'id={city_id}&mode=json&appid={app.config["OPENWEATHERMAP_API_KEY"]}'
