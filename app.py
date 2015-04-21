from flask import Flask, request, render_template, url_for, redirect, flash, session, g, send_file, abort
from sqlalchemy.exc import IntegrityError




app = Flask(__name__)

app.config.from_object('config')




@app.route('/')
def index():
    return render_template('index.html',page="home")


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8888)
