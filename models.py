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