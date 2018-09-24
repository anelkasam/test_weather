from app import db
from app import login
from datetime import datetime
from flask_login import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    country = db.Column(db.String(5), index=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    forecasts = db.relationship('Forecast', backref='city', lazy=True)

    def __repr__(self):
        return f'{self.id}: {self.name} {self.country} ({self.lat}{self.lon})'


class Forecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    data_time = db.Column(db.DateTime, index=True)
    temperature = db.Column(db.Float)
    windSpeed = db.Column(db.Float)
    clouds = db.Column(db.String(50))
    pressure = db.Column(db.Float)
    description = db.Column(db.String(80))

    def __repr__(self):
        city = City.query.get(self.city_id)
        return f'Forecast for {city} on {self.data_time}: '


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
