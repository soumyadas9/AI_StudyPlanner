from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()  # THIS MUST EXIST AT THE TOP

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    streak = db.Column(db.Integer, default=0)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    difficulty = db.Column(db.Integer)
    estimated_time = db.Column(db.Float)
    deadline = db.Column(db.Date)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100))
    hours_spent = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
