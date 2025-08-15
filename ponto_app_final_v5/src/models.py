from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
class RegistroPonto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Date, default=date.today, nullable=False)

    entrada = db.Column(db.Time, nullable=True)
    saida_almoco = db.Column(db.Time, nullable=True)
    retorno_almoco = db.Column(db.Time, nullable=True)
    saida_final = db.Column(db.Time, nullable=True)

    entrada_lat = db.Column(db.Float, nullable=True)
    entrada_lng = db.Column(db.Float, nullable=True)

    saida_almoco_lat = db.Column(db.Float, nullable=True)
    saida_almoco_lng = db.Column(db.Float, nullable=True)

    retorno_almoco_lat = db.Column(db.Float, nullable=True)
    retorno_almoco_lng = db.Column(db.Float, nullable=True)

    saida_final_lat = db.Column(db.Float, nullable=True)
    saida_final_lng = db.Column(db.Float, nullable=True)

    banco_horas = db.Column(db.Float, nullable=True)
