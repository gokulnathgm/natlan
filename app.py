from flask import Flask, request, render_template, url_for, redirect, flash, session, g, send_file, abort
from sqlalchemy.exc import IntegrityError
from textblob import TextBlob
import json,nltk,urllib2,re,pattern.en,calendar


app = Flask(__name__)

app.config.from_object('config')
from models import Properties,History
from models import db

db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		history = History.query.order_by(History.id.desc()).limit(9)
		return render_template('index.html',page="home",history=history)
	elif request.method == 'POST':
		history = History.query.order_by(History.id.desc()).limit(5)
		des = False
		app.logger.info(repr(request.form))
		question = request.form['question']
		#q_tagged = pattern.en.tag(question)				#tags the question
		blob = TextBlob(question)
		q_tagged = blob.tags
		app.logger.info(repr(q_tagged))
		
		grammar = r"""NP: {<JJ.*>*<IN>*<NN.*>+}
					{<NN.*><IN>+<JJ.*>+}"""	
									#grammar for chunking
		np_parser = nltk.RegexpParser(grammar)
		np_tree = np_parser.parse(q_tagged)

		q_noun = []

		for i in np_tree:								#to get all the Noun Phrases to q_noun
   			NPs=""
   			if str(type(i))=="<class 'nltk.tree.Tree'>":		
   				for k in i:
   					if k[1]=="IN":
   						continue
   					else:
   						if NPs=="":
   							NPs=k[0]
   						else:
   							NPs=NPs+" "+k[0]


   				q_noun.append(NPs)

		app.logger.info(repr(q_noun))

		"""conjuction = ["with","by","of","in","as","if","as if","even","than","that","until","and","but","or","nor","for","yet","so"]
		for idx,i in enumerate(q_noun):					#add + in btwn words for searching
			for j in conjuction:
				q_noun[idx] = re.sub('\s'+j+'\s','',q_noun[idx], flags=re.IGNORECASE)
				q_noun[idx] = re.sub('^'+j+'\s','',q_noun[idx], flags=re.IGNORECASE)
				q_noun[idx] = re.sub('\s'+j+'$','',q_noun[idx], flags=re.IGNORECASE)"""
									
		app.logger.info(repr(q_noun))
		noun_save = ""
		for a in q_noun:
			noun_save += " | " + a

		
		app.logger.info(repr(history))

		ques = History.query.filter_by(q_noun = noun_save).first()
		if ques:
			value = {'question':question,'answer':ques.answer}
			flash(value,'success')
			return render_template('index.html',page="home",history=history)
		

		b=False
		pty =[]

		if len(q_noun) == 1:
			des = True
			pty=Properties.query.filter(Properties.pid == "P31").all()

		else:
			ptyl = False
			for idx,i in enumerate(q_noun):			#search for property in the DB with 2 entries of q_noun
				for jdx, j in enumerate(q_noun[idx+1:]):
					ptyl = Properties.query.filter(Properties.label.like("%"+i+"%"+j+"%")).all()		#searches in label

					if not ptyl:
						ptyl = Properties.query.filter(Properties.aliases.like("%"+i+"%"+j+"%")).all()		#search in aliases

					if ptyl:
						for k in range(len(ptyl)):											#Strict comparison if >1 ptys found
							if ptyl[k].label.lower() == i.lower():
								pty.append(ptyl[k])
								b=True
								app.logger.info(repr("pty found by exact property"))
								break

						if not b:
							pty = ptyl
						app.logger.info(repr(pty))
						del q_noun[idx]
						del q_noun[jdx]
						app.logger.info(repr("pty found by double property"))
						break


			if not ptyl:										#search for property in the DB with single entry of q_noun
				for idx,i in enumerate(q_noun):	
					ptyl = Properties.query.filter(Properties.label.like("%"+i+"%")).all()		#searches in label

					if not ptyl:
						ptyl = Properties.query.filter(Properties.aliases.like("%"+i+"%")).all()		#search in aliases

					if ptyl:
						for k in range(len(ptyl)):											#Strict comparison if >1 ptys found
							if ptyl[k].label.lower() == i.lower():
								pty.append(ptyl[k])
								b=True
								app.logger.info(repr(i))
								break
						if not b:
							pty = ptyl
						app.logger.info(repr(pty))
						del q_noun[idx]
						app.logger.info(repr("pty found by single property"))
						break
						

		if not pty:	
			val = {'question':question,'answer':"Sorry... Property not found"}								#property doesnt exist if pid is empty
			flash(val,'warning')
			return render_template('index.html',page="home",history=history)


		if not q_noun:									#no entries to search
			val = {'question':question,'answer':"Please make sure that the Question is Correct.."}
			flash(val,'warning')
			return render_template('index.html',page="home",history=history)

		
		for idx,i in enumerate(q_noun):					#add + in btwn words for searching
			app.logger.info(repr(str(q_noun[idx])))
			x=str(q_noun[idx]).replace(" ","+")
			q_noun[idx]=x
			

		app.logger.info(repr(q_noun))


		"""finds Entity id (Qid) for elements in q_noun, searches till atleast one result is obtained"""
		qid = False
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
				break
		
		if not qid:
			val = {'question':question,'answer':"Sorry... Can't find anything.."}
			flash(val,'warning')
			return render_template('index.html',page="home",history=history)


		"""find entity using qid"""

		ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
		response = urllib2.urlopen(ur)
		data = json.load(response)

		if des == True:
			value = data['entities'][qid]['descriptions']['en']['value']
			val = {'question':question,'answer':value}
			flash(val,'success')
			saveqa(question,noun_save,value)
			return render_template('index.html',page="home",history=history)

		else:

			if 'claims' in data['entities'][qid]:			#checks whether entity has any statements
				
				for prop in pty:
					pid = prop.pid
					app.logger.info(repr("Pid  : "+pid))
					
					if pid in data['entities'][qid]['claims']:	#checks whether entity has the given property
						app.logger.info(repr("pid = " + str(pid)))
						obj = data['entities'][qid]['claims'][pid][0]['mainsnak']['datatype']
						app.logger.info(repr(obj))
						if obj == "wikibase-item":				#property value is another entity
							value=""
							ct=0
							for i in range(len(data['entities'][qid]['claims'][pid])):	
										#gets value from property page
								if ct>0:
									value=value+", "		
								value_id = data['entities'][qid]['claims'][pid][i]['mainsnak']['datavalue']['value']['numeric-id']
								app.logger.info(repr(value_id))
							
								u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
								response1 = urllib2.urlopen(u)
								data2 = json.load(response1)
								ct+=1
								if data2['success']:
									value = value+""+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
								else:
									val = {'question':question,'answer':"Sorry... Value can't be found.."}
									flash(val,'warning')
									return render_template('index.html',page="home",history=history)

							val = {'question':question,'answer':value}
							flash(val,'success')
							saveqa(question,noun_save,value)
							return render_template('index.html',page="home",history=history)

						elif obj == "string" or obj == "url":			#if property value is string or url
							value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']
							val = {'question':question,'answer':value}
							flash(val,'success')
							saveqa(question,noun_save,value)
							return render_template('index.html',page="home",history=history)
						
						elif obj == "globe-coordinate":					#if property value is geo coordinates
							latvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['latitude']
							lonvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['longitude']
							value = "latitude: {} longitude: {} ".format(latvalue,lonvalue)
							val = {'question':question,'answer':value}
							flash(val,'success')
							saveqa(question,noun_save,value)
							return render_template('index.html',page="home",history=history)

						elif obj == "time":
							time = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['time']
							time = time.split('-')
							year = time[0][8:12]
							day = time[2][:2]
							month = calendar.month_name[int(time[1])]
							value = "{}th {} {}".format(day,month,year)
							val = {'question':question,'answer':value}
							flash(val,'success')
							saveqa(question,noun_save,value)
							return render_template('index.html',page="home",history=history)

						else:											#for all other property values
							value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['amount']
							val = {'question':question,'answer':value}
							flash(val,'success')
							saveqa(question,noun_save,value)
							return render_template('index.html',page="home",history=history)

				val = {'question':question,'answer':"Sorry... Property not found"}
				flash(val,'warning')
				return render_template('index.html',page="home",history=history)

			else:
				val = {'question':question,'answer':"Sorry... Can't find anything"}
				flash(val,'warning')
				return render_template('index.html',page="home",history=history)


def saveqa(question,q_noun,answer):
	q = History(question,q_noun,answer)
	db.session.add(q)
	db.session.commit()



if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050)
