import json
import requests

from datetime import datetime
from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm, CitySearchForm
from app.models import User, City, Forecast
from app.utils import plot_forecast


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
    temp_delta = 273.15
    city = City.query.get(city_id)
    forecasts = Forecast.query.filter(Forecast.city_id == city.id,
                                      Forecast.data_time >= datetime.now()).all()
    context = {'city': city,
               'history': Forecast.query.filter(Forecast.city_id == city.id,
                                                Forecast.data_time < datetime.now()).all()}

    forecast_params = {'id': city_id,
                       'mode': 'json',
                       'appid': app.config["OPENWEATHERMAP_API_KEY"]}
    forecast_data = requests.get('http://api.openweathermap.org/data/2.5/forecast',
                                 params=forecast_params).json()
    if forecast_data['cod'] != '200':
        return render_template('weather.html', context=context)

    forecast_objs = []
    for data in forecast_data['list']:
        forecast = Forecast(city_id=city.id,
                            data_time=datetime.fromtimestamp(data['dt']),
                            temperature=int(data['main']['temp'] - temp_delta),
                            temperature_min=int(data['main']['temp_min'] - temp_delta),
                            temperature_max=int(data['main']['temp_max'] - temp_delta),
                            windSpeed=data['wind']['speed'],
                            clouds=data['clouds']['all'],
                            pressure=data['main']['pressure'],
                            description=', '.join(d['description'] for d in data['weather']))
        forecast_objs.append(forecast)
        if forecast not in forecasts:
            db.session.add(forecast)
    db.session.commit()

    context['forecast'] = forecast_objs
    context['forecast_plots'] = plot_forecast(forecast_objs)
    context['history_plots'] = plot_forecast(context['history'])
    return render_template('weather.html', context=context)
