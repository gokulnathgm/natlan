from flask import Flask, request, render_template, url_for, redirect, flash, session, g, send_file, abort
from sqlalchemy.exc import IntegrityError
from textblob import TextBlob
import json,nltk,urllib2,re,pattern.en,calendar,wikipedia


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


		keys = []
		key = ""
		for k in q_noun:
			keys.append(k)

		for k in keys:
			key = key+" "+k

	
		b=False
		pty =[]

		if len(q_noun) == 1:
			q_noun1=q_noun[:]
			app.logger.info(repr(q_noun1))
			q_noun=[]
			grammar=r"""NP:{<JJ.*>*<NN.*>+<VB.*><IN>?}"""
			np_parser = nltk.RegexpParser(grammar)
			np_tree = np_parser.parse(q_tagged)
			app.logger.info(repr(np_tree))
			for i in np_tree:								#to get all the Noun Phrases to q_noun
   				NPs=""
   				if str(type(i))=="<class 'nltk.tree.Tree'>":		
   					for k in i:
   						a = re.compile("VB.*")
						if a.match(k[1]):
   						#if k[1]=="VB.*":
   							q_noun.append(NPs)
   							NPs=""
   				
   						if NPs=="":
   							NPs=k[0]
   						else:
   							NPs=NPs+" "+k[0]
   				
   					q_noun.append(NPs)
   			app.logger.info(repr(q_noun))
   			if not q_noun:
   				q_noun=q_noun1[:]
   				des = True
				pty=Properties.query.filter(Properties.pid == "P31").all()
		
   		
   		app.logger.info(repr(q_noun))
		noun_save = ""
		for a in q_noun:
			noun_save += " | " + a.lower()

		
		app.logger.info(repr(history))

		ques = History.query.filter_by(q_noun = noun_save).first()
		if ques:
			value = {'question':question,'answer':ques.answer, 'content' : ques.content}
			flash(value,'success')
			return render_template('index.html',page="home",history=history)

			#des = True
			#pty=Properties.query.filter(Properties.pid == "P31").all()
		if not des:
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
				answer = searchwiki(key,"")
				val = {'question':question,'answer':answer, 'content' : "string"}								#property doesnt exist if pid is empty
				flash(val,'warning')
				return render_template('index.html',page="home",history=history)


		if not q_noun:									#no entries to search
			val = {'question':question,'answer':"Please make sure that the Question is Correct..", 'content' : "string"}
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
			val = {'question':question,'answer':"Sorry... Can't find anything..", 'content' : "string"}
			flash(val,'warning')
			return render_template('index.html',page="home",history=history)


		"""find entity using qid"""

		ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
		response = urllib2.urlopen(ur)
		data = json.load(response)

		if des == True:
			value = data['entities'][qid]['descriptions']['en']['value']
			if value == "Wikipedia disambiguation page" or value == "Wikimedia disambiguation page":
				value = searchwiki(key,value)
			val = {'question':question,'answer':value , 'content' : "string"}
			flash(val,'success')
			saveqa(question,noun_save,value,"string")
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
									val = {'question':question,'answer':"Sorry... Value can't be found..", 'content' : "string"}
									flash(val,'warning')
									return render_template('index.html',page="home",history=history)

							val = {'question':question,'answer':value , 'content' : "string"}
							flash(val,'success')
							saveqa(question,noun_save,value,"string")
							return render_template('index.html',page="home",history=history)

						elif obj == "string" or obj == "url":			#if property value is string or url
							value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']
							val = {'question':question,'answer':value , 'content' : "string"}
							flash(val,'success')
							saveqa(question,noun_save,value,"string")
							return render_template('index.html',page="home",history=history)
						
						elif obj == "globe-coordinate":					#if property value is geo coordinates
							latvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['latitude']
							lonvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['longitude']
							value = "latitude: {} longitude: {} ".format(latvalue,lonvalue)
							val = {'question':question,'answer':value , 'content' : "string"}
							flash(val,'success')
							saveqa(question,noun_save,value,"string")
							return render_template('index.html',page="home",history=history)

						elif obj == "time":
							time = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['time']
							time = time.split('-')
							year = time[0][1:]
							day = time[2][:2]
							month = calendar.month_name[int(time[1])]
							value = "{}th {} {}".format(day,month,year)
							val = {'question':question,'answer':value , 'content' : "string"}
							flash(val,'success')
							saveqa(question,noun_save,value,"string")
							return render_template('index.html',page="home",history=history)
						elif obj=="commonsMedia":
							value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']
							value = value.replace(" ","_")	
							app.logger.info(repr(value))						
							ur = "http://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=Image:"+value+"&iiprop=url&format=json"
							response1 = urllib2.urlopen(ur)
							data2 = json.load(response1)
							for a in data2['query']['pages']:
								url = data2['query']['pages'][a]['imageinfo'][0]['url']
								break 
							if url:
								val= {'question':question,'answer':url , 'content' : "media" }
								flash(val,'success')
								saveqa(question,noun_save,url,"media")
								return render_template('index.html',page="home",history=history)

							val= {'question':question,'answer':"Sorry... Media not found"}
							flash(val,'warning')
							return render_template('index.html',page="home",history=history)
						elif obj=="monolingualtext":
							value= data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['text']
							val = {'question':question,'answer':value}
							flash(val,'success')
							saveqa(question,noun_save,value,"string")
							return render_template('index.html',page="home",history=history)


						else:											#for all other property values
							value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['amount']
							val = {'question':question,'answer':value , 'content' : "string"}
							flash(val,'success')
							saveqa(question,noun_save,value,"string")
							return render_template('index.html',page="home",history=history)

				
				answer = searchwiki(key,"")			
				val = {'question':question,'answer':answer, 'content' : "string"}
				flash(val,'warning')
				return render_template('index.html',page="home",history=history)

			else:
				answer = searchwiki(key,"")
				val = {'question':question,'answer':answer, 'content' : "string"}
				flash(val,'warning')
				return render_template('index.html',page="home",history=history)


def saveqa(question,q_noun,answer,content):
	q = History(question,q_noun,answer,content)
	db.session.add(q)
	db.session.commit()

def searchwiki(question,value):
	key = wikipedia.search(question)
	if value=="Wikipedia disambiguation page" or value=="Wikimedia disambiguation page":
		m = wikipedia.page(wikipedia.search(key[0]))
		answer = wikipedia.summary(m.title,sentences=1)
	else:
		answer = wikipedia.summary(key[0],sentences=1)
	app.logger.info(repr(key[0]))
	return answer



if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050)
