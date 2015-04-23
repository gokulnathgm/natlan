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
			if re.search('^N', k):
				q_noun.append(i[0])

		app.logger.info(repr(q_noun))

		for idx,i in enumerate(q_noun):
			pty = Properties.query.filter(Properties.label.like("%"+i+"%")).first()
			if pty:
				app.logger.info(repr(pty))
				pid = pty.pid
				app.logger.info(repr(pid))
				del q_noun[idx]
			else:
				flash("Property not found",'warning')
				return render_template('index.html',page="home")

		if not q_noun:
			flash("Please make sure that the Question is Correct..",'warning')
			return render_template('index.html',page="home")

		for i in q_noun:
			ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
			response = urllib2.urlopen(ur)
			data = json.load(response)
			app.logger.info(repr(i))
			if data['success']:
				qid = data['search'][0]['id']
				app.logger.info(repr("Qid  : "+qid))
			else:
				flash("Item not found",'warning')
				return render_template('index.html',page="home")


		ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
		response = urllib2.urlopen(ur)
		data = json.load(response)
		if data['success']:
			obj = data['entities'][qid]['claims'][pid][0]['mainsnak']['datatype']
			if obj == "wikibase-item":
				value_id = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['numeric-id']
				app.logger.info(repr(value_id))
				
				u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
				response1 = urllib2.urlopen(u)
				data2 = json.load(response1)
				if data2['success']:
					value = data2['entities']['Q'+str(value_id)]['labels']['en']['value']
					flash(value,'success')
					return render_template('index.html',page="home")
				else:
					flash("Item not found",'warning')
					return render_template('index.html',page="home")
			else:
				value = data['entities'][qid]['claims'][pid][0]['mainsnak']['value']
				flash(value,'success')
				return render_template('index.html',page="home")

		else:
			flash("Item not found",'warning')
			return render_template('index.html',page="home")


    




if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050)
