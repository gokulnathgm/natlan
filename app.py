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

		grammar = "NP: {<JJ.*>*<NN.*>+}"
		np_parser = nltk.RegexpParser(grammar)
		np_tree = np_parser.parse(q_tagged)

		q_noun = []

		for i in np_tree:
   			NPs=""
   			if str(type(i))=="<class 'nltk.tree.Tree'>":
   				for k in i:
   					if NPs=="":
   						NPs=k[0]
   					else:
   						#NPs=NPs+"+"+k[0]
   						NPs=NPs+" "+k[0]


   				q_noun.append(NPs)

		"""for i in q_tagged:
			k=i[1]
			if re.search('^N', k):
				q_noun.append(i[0])"""

		app.logger.info(repr(q_noun))
		b=False
		for idx,i in enumerate(q_noun):
			ptyl = Properties.query.filter(Properties.label.like("%"+i+"%")).all()

			for k in range(len(ptyl)):
				app.logger.info(repr(ptyl[k].label))
				if ptyl[k].label.lower() == i.lower():
					pid = ptyl[k].pid
					b=True
					del q_noun[idx]
					break

			if b==False:
				pty=ptyl[0]


			#if pty:
				app.logger.info(repr(pty))
				pid = pty.pid
				app.logger.info(repr(pid))
				del q_noun[idx]
				#break
			#else:
				#flash("Property not found",'warning')
				#return render_template('index.html',page="home")

		for idx,i in enumerate(q_noun):
			app.logger.info(repr(str(q_noun[idx])))
			x=str(q_noun[idx]).replace(" ","+")
			q_noun[idx]=x
			

		app.logger.info(repr(q_noun))
		app.logger.info(repr(pid))


		if not q_noun:
			flash("Please make sure that the Question is Correct..",'warning')
			return render_template('index.html',page="home")

		"""always assigns the last word in the q_noun as Qid"""	
		for i in q_noun:
			ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
			app.logger.info(repr(ur))
			response = urllib2.urlopen(ur)
			data = json.load(response)
			app.logger.info(repr(i))
			if data['search']:
				app.logger.info(repr(data))
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
				value=""
				for i in range(len(data['entities'][qid]['claims'][pid])):

					value_id = data['entities'][qid]['claims'][pid][i]['mainsnak']['datavalue']['value']['numeric-id']
					app.logger.info(repr(value_id))
				
					u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
					response1 = urllib2.urlopen(u)
					data2 = json.load(response1)
					if data2['success']:
						value = value+"  "+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
				flash(value,'success')
				return render_template('index.html',page="home")
					#else:
					#	flash("Item not found",'warning')
					#	return render_template('index.html',page="home")

			elif obj == "string":
				value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']
				flash(value,'success')
				return render_template('index.html',page="home")

			elif obj == "url":
				value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']
				flash(value,'success')
				return render_template('index.html',page="home")

			elif obj == "globe-coordinate":
				latvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['latitude']
				lonvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['longitude']
				value = "latitude: {} longitude: {} ".format(latvalue,lonvalue)
				flash(value,'success')
				return render_template('index.html',page="home")

			else:
				value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['amount']
				flash(value,'success')
				return render_template('index.html',page="home")

		else:
			flash("Item not found",'warning')
			return render_template('index.html',page="home")


    




if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050)
