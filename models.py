from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Properties(db.Model):
    """Properties and id"""
    __tablename__ = "property"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String, nullable=False)
    pid = db.Column(db.String, nullable=False)

    def __init__(self, label, pid):
        self.label = label
        self.pid = pid