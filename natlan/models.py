from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Properties(db.Model):
    """Properties and id"""
    __tablename__ = "property"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, nullable=False)
    pid = db.Column(db.String, nullable=False)
    aliases = db.Column(db.String, nullable=True)

    def __init__(self, label, pid, aliases):
        self.label = label
        self.pid = pid
        self.aliases = aliases


class History(db.Model):
    """History of Questions and answers"""
    __tablename__ = "history"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    q_noun = db.Column(db.String, nullable=False)
    answer = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)

    def __init__(self, question, q_noun, answer,content):
        self.question = question
        self.q_noun = q_noun
        self.answer = answer
        self.content = content