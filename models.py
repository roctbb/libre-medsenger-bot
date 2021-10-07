from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

db = SQLAlchemy()


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_import = db.Column(db.DateTime, nullable=True)
    name = db.Column(db.String(255), nullable=True)
    birthday = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)

    yellow_top = db.Column(db.Float, nullable=True)
    yellow_bottom = db.Column(db.Float, nullable=True)
    red_top = db.Column(db.Float, nullable=True)
    red_bottom = db.Column(db.Float, nullable=True)
