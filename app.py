from flask import Flask, request, render_template, url_for, redirect, flash, session, g, send_file, abort
from sqlalchemy.exc import IntegrityError
import json,nltk,urllib2,re


app = Flask(__name__)

app.config.from_object('config')
from models import Properties
from models import db

db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
	    return render_template('index.html',page="home")
	elif request.method == 'POST':
		app.logger.info(repr(request.form))
		question = request.form['question']
		q_tokens = nltk.word_tokenize(question)
		q_tagged = nltk.pos_tag(q_tokens)
		q_noun = []

		for i in q_tagged:
			k=i[1]
			if re.search('^N.', k):
				app.logger.info(repr(i[0]))
				q_noun.append(i[0])

		for idx,i in enumerate(q_noun):
			pty = Properties.query.filter(Properties.label.like("%"+i+"%")).first():
			if pty:
				pid = pty.pid
				del q_noun[idx]
			else
				flash("Property not found",'warning')
				return render_template('index.html',page="home")

		for i in q_noun
			ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
				response = urllib2.urlopen(ur)
				data = json.load(response)
				if data['success'] == 1:
					qid = data['search'][0]['id']
				else
					flash("Item not found",'warning')
					return render_template('index.html',page="home")


		ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
			response = urllib2.urlopen(ur)
			data = json.load(response)
			if data['success'] == 1:
				obj = data['entities'][qid]['claims'][pid][0]['mainsnak']['datatype']
				if obj == "wikibase-item":
					u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+obj+"&format=json&language=en"
					response1 = urllib2.urlopen(u)
					data1 = json.load(response1)
					data1['entities']['Q668']['claims']['P36'][0]['mainsnak']['datavalue']['value']['numeric-id']






			else
				flash("Item not found",'warning')
				return render_template('index.html',page="home")


        




if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8888)
