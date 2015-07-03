from flask import Flask, request, render_template, url_for, redirect, flash, session, g, send_file, abort
from sqlalchemy.exc import IntegrityError
from textblob import TextBlob
import json,nltk,urllib2,re,pattern.en,calendar,wikipedia
from math import radians, cos, sin, asin, sqrt
from datetime import date,datetime

app = Flask(__name__)

app.config.from_object('config')
from models import Properties,History
from models import db

db.init_app(app)

question = ""

@app.route('/', methods=['GET', 'POST'])

def index():
	global question
	if request.method == 'GET':
		history = History.query.order_by(History.id.desc()).limit(9)
		return render_template('index.html',page="home",history=history)
	elif request.method == 'POST':
		history = History.query.order_by(History.id.desc()).limit(5)
		
		app.logger.info(repr(request.form))
		question = request.form['question']
		question = question.replace('?','')
		
		blob = TextBlob(question)				#tags the question
		q_tagged = blob.tags
		app.logger.info(repr(q_tagged))

		parsed = parse(q_tagged)
		q_noun = parsed['q_noun']
		typ = parsed['type']
		noun_save = parsed['noun_save']

		ques = History.query.filter_by(q_noun = noun_save).first()
		if ques:
			if ques.content == "list":
				answer = []
				word=""
				for i in ques.answer:
					if i == ",":

						answer.append(word)
						word=""
					else:
						word = word+str(i)
				answer = [tuple(answer[i:i+3]) for i in range(0, len(answer), 3)]
				app.logger.info(repr(answer))
			else:
				answer = ques.answer


			value = {'question':question,'answer':answer, 'content' : ques.content}
			typ = "From history"


		if typ == "keyword":
			app.logger.info(repr("keyword"))
			quest = []
			quest.append(question)
			searched = wikidata_search(quest)
			qid = searched['qid']

			if qid == False:
				answer = searchwiki(question.replace(' ','+'))
				if answer == False:
					answer = "As of now, the System is unable to answer the question."

			else:
				app.logger.info(repr(qid))
				data = wikidata_get_entity(qid)
				if 'description' in data['entities'][qid]:
					answer = data['entities'][qid]['description']['en']['value']
				else:
					answer = data['entities'][qid]['descriptions']['en']['value']

			value = {'question':question,'answer':answer, 'content' : "string"}


		if typ == "list":
			app.logger.info(repr("list"))
			
			np_tree=parsed['np_tree']
			value = get_list(q_noun,np_tree)
			if value==True:
				value = "As of now, the System is unable to answer the question."
				value = {'question':question,'answer':answer, 'content' : "string"}
		if typ == "general":
			app.logger.info(repr("general"))
			result = get_property(q_noun)
			if result:
				pty = result['property']
				q_noun = result['q_noun']
				value = get_general(q_noun,pty)
			else:
				answer = "As of now, the System is unable to answer the question."
				value = {'question':question,'answer':answer, 'content' : "string"}
			
		if typ == "distance":
			app.logger.info(repr("distance"))
			value = get_distance(q_noun)
			if not value:
				answer = "As of now, the System is unable to answer the question."
				value = {'question':question,'answer':answer, 'content' : "string"}
		if typ == "time":
			app.logger.info(repr("time"))
			answer = get_date(q_noun)
			value = {'question':question,'answer':answer, 'content' : "string"}

		if typ == "description":
			app.logger.info(repr("description"))
			value = get_description(q_noun)
			if not value:
				value = {'question':question,'answer':"As of now, the System is unable to answer the question.", 'content' : "string"}

		if typ !="From history":
			answer = ""
			if value['content']=="list":
				for jdx,j in enumerate(value['answer']):
					for i in value['answer'][jdx]:
						answer += str(i) + ", "
				saveqa(question,noun_save,answer,value['content'])
			else:
				saveqa(question,noun_save,value['answer'],value['content'])
			
		flash(value,'success')
		app.logger.info(repr(value))
		return render_template('index.html',page="home",history=history)




def parse(q_tagged):
	grammars=[r"""NP: {<JJ.*>*<NNS><IN>+<DT>*<NN.*>+}""",r"""NP: {<JJ.*>*<IN>*<NN.*>+}
	{<NN.*><IN>+<JJ.*>+}
	{<IN>*<CD>+}""",r"""NP:{<JJ.*>*<NN.*>+<VB.*><IN>?}"""]
	j=0
	q_noun=[]
	for grammar in grammars:
		grmr=j
		app.logger.info(repr(grammar))
		np_parser = nltk.RegexpParser(grammar)
		np_tree = np_parser.parse(q_tagged)
		q_noun = []	
		app.logger.info(repr(np_tree))
		for i in np_tree:	
			app.logger.info(repr("NP : " + str(i)))						#to get all the Noun Phrases to q_noun
			NPs=""
			if str(type(i))=="<class 'nltk.tree.Tree'>":		
				for k in i:
					if j==0:
						if k[1]=="NNS":
							t=pattern.en.singularize(k[0])
						else:
							t=k[0]
					elif j==1:
						if k[1]=="IN":
							continue
						else:
							t=k[0]
					elif j==2:
						a = re.compile("VB.*")
						if a.match(k[1]):
   							q_noun.append(NPs)
   							NPs=""
   						t=k[0]

					if NPs=="":
						NPs=t
					else:
						NPs=NPs+" "+t
						app.logger.info(repr("NPs : " + str(NPs)))

				q_noun.append(NPs)
				app.logger.info(repr("q_noun : " + str(q_noun)))
		if (q_noun and j==0) or (len(q_noun)!=1 and j==1):
			break
		if j==1 and len(q_noun)==1:
			q_noun1=q_noun[:]
		if j==2 and not q_noun:
			q_noun=q_noun1[:]

		j+=1

		app.logger.info(repr(q_noun))
		app.logger.info(repr("grmr :"+str(grmr)))




	grammar = {'q_noun':q_noun, 'grammar':grmr,'np_tree':np_tree}

	parsed = qcheck(grammar)
	noun_save = ""
	for a in q_noun:
		noun_save += " | " + a.lower()

	parsed['noun_save'] = noun_save

	return parsed

def qcheck(parsed):
	q_noun = parsed['q_noun']
	grmr = parsed['grammar']

	if not q_noun:
		return {'q_noun':q_noun,'type':"keyword"}

	if grmr==0:
		np_tree=parsed['np_tree']
		return {'q_noun':q_noun,'type':"list",'np_tree':np_tree}

	if len(q_noun)==1 and grmr==2:
		des = True
		qid = False
		for idx,i in enumerate(q_noun):					#add + in btwn words for searching
			app.logger.info(repr(str(q_noun[idx])))
			x=str(q_noun[idx]).replace(" ","+")
			q_noun[idx]=x
		return {'q_noun':q_noun,'type':"description"}
	
	
	rng = False
	dt = False
	for idx,k in enumerate(q_noun):
		if 'distance' in k or 'length' in k or 'long' in k or 'kilometers'in k or 'how far' in question:
			rng = True
			del q_noun[idx]

	if rng:
		for idx,i in enumerate(q_noun):
			q_noun[idx] = q_noun[idx].replace(' ','+')
		return {'q_noun':q_noun,'type':"distance"}

	if ('days' in question and 'between' in question) or ('time' in question and 'duration' in question) :
		dt = True
		return {'q_noun':q_noun,'type':"time"}

	if grmr==2 or grmr==1:
		return {'q_noun':q_noun,'type':"general"}


def wikidata_search(q_noun):
	qid = False
	for idx,i in enumerate(q_noun):					#add + in btwn words for searching
		app.logger.info(repr(str(q_noun[idx])))
		x=str(q_noun[idx]).replace(" ","+")
		q_noun[idx]=x
	
	for idx,i in enumerate(q_noun):			
		ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
		app.logger.info(repr(ur))
		response = urllib2.urlopen(ur)
		data = json.load(response)
		if data['search']:
			app.logger.info(repr("wikidata search : " + i ))
			if 'description' in data['search'][0]:
				if data['search'][0]['description'] == 'Wikipedia disambiguation page' or data['search'][0]['description'] == 'Wikimedia disambiguation page':
					qid = data['search'][1]['id']
				else:
					qid = data['search'][0]['id']
			else:
				qid = data['search'][0]['id']
			app.logger.info(repr("Qid  : "+qid))
			break
	if not qid:
		qid=False
	return {'q_noun':q_noun,'qid':qid}

def wikidata_get_entity(qid):
	ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
	response = urllib2.urlopen(ur)
	return json.load(response)

def get_list(q_noun,np_tree):
	wikidatasearch = wikidata_search(q_noun)
	list_direct=True
	list_position=False
	list_instance=False
	gr=False
	if wikidatasearch['qid']:
		qid = wikidatasearch['qid']
		q_noun = wikidatasearch['q_noun']

		qid1=qid[1:]
		qid=qid1[:]
		app.logger.info(repr(qid))
		ur="https://wdq.wmflabs.org/api?q=claim[39:"+qid+"]"
		app.logger.info(repr(ur))
		response = urllib2.urlopen(ur)
		data = json.load(response)
	
		ct=0
		if data['status']['items']!=0:
			list_position=True

		else:
			ur="https://wdq.wmflabs.org/api?q=claim[31:"+qid+"]"
			app.logger.info(repr(ur))
			response = urllib2.urlopen(ur)
			data = json.load(response)
			ct=0
			if data['status']['items']!=0:
				list_instance=True
		if list_position or list_instance:
			value=[]
			value1=""
			for i in range(len(data['items'])):	
				#gets value from property page

				value_id = data['items'][i]
				app.logger.info(repr(value_id))
									
				data2 = wikidata_get_entity("Q"+str(value_id))
				ct+=1
				if data2['success']:
					if 'labels' in data2['entities']['Q'+str(value_id)]:
						if ct>0:
							value1=value1+", "	
						value.append(data2['entities']['Q'+str(value_id)]['labels']['en']['value'])
						value1=value1+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
					else:
						continue
		else:
			list_direct=False

	elif not wikidatasearch['qid'] or list_direct==False:
		error = False
		for i in np_tree:
			NPs=""
			nou=""
			s=False
			if str(type(i))=="<class 'nltk.tree.Tree'>":
				for k in i:
					if k[1]!="IN" and s==False:
						if k[1]=="NNS":
							t=pattern.en.singularize(k[0])
						else:
							t=k[0]
						if NPs=="":
							NPs=t
						else:
							NPs=NPs+"+"+t
					elif k[1]=="IN":
						s=True
						continue
					if s==True:
						if nou=="":
							nou=k[0]
						else:
							nou=nou+"+"+k[0]

		wikidatasearch=wikidata_search([NPs])
		if wikidatasearch['qid']:
			qid=wikidatasearch['qid']
			app.logger.info(repr("Qid  : "+qid))
		else:
			qid = False
			error = True

		wikidatasearch=wikidata_search([nou])
		if wikidatasearch['qid']:
			qid1=wikidatasearch['qid']
			app.logger.info(repr("Qid  : "+qid1))
		else:
			qid1 = False
			error = True
		if not error:
			data = wikidata_get_entity(qid1)
			if 'claims' in data['entities'][qid1]:
				obj = data['entities'][qid1]['claims']['P31'][0]['mainsnak']['datatype']
				app.logger.info(repr(obj))
				if obj == "wikibase-item":				#property value is another entity
					for i in range(len(data['entities'][qid1]['claims']['P31'])):	
						#gets value from property page	
						value_id = data['entities'][qid1]['claims']['P31'][i]['mainsnak']['datavalue']['value']['numeric-id']
						app.logger.info(repr(value_id))
						pty=[]	
						ptyl=[]
						b=False

						data2 = wikidata_get_entity("Q"+str(value_id))
						if data2['success']:
							value = data2['entities']['Q'+str(value_id)]['labels']['en']['value']
							ptyl = Properties.query.filter(Properties.label.like("%"+value+"%")).all()		#searches in label
							if not ptyl:
								ptyl = Properties.query.filter(Properties.aliases.like("%"+value+"%")).all()		#search in aliases

							if ptyl:
								for k in range(len(ptyl)):											#Strict comparison if >1 ptys found
									if ptyl[k].label.lower() == value.lower():			#or value.lower() in ptyl[k].aliases.lower():
										pty = ptyl[k]
										b=True
										app.logger.info(repr(value))
										break
								if not b:
									continue
								app.logger.info(repr("pty found" + str(pty)))
								pid = pty.pid
								
								ur="https://wdq.wmflabs.org/api?q=claim[31:"+qid[1:]+"]%20and%20claim["+pid[1:]+":"+qid1[1:]+"]"
								response = urllib2.urlopen(ur)
								data = json.load(response)
								value=[]
								value1=""
								ct=0
								if data['status']['items']!=0:
									gr=True
										
									for i in range(len(data['items'])):	
										#gets value from property page
												
										value_id = data['items'][i]
										app.logger.info(repr(value_id))
													

										data2 = wikidata_get_entity("Q"+str(value_id))
										ct+=1
										if data2['success']:
											if 'labels' in data2['entities']['Q'+str(value_id)]:
												if ct>0:
													value1=value1+", "
												value.append(data2['entities']['Q'+str(value_id)]['labels']['en']['value'])
												value1+=data2['entities']['Q'+str(value_id)]['labels']['en']['value']
											else:
												continue
									break	
								else:
									continue
							else:
								error = True
								
						else:
							continue
				else:
					error = True
			else:
				error = True
	if gr or list_direct:
		app.logger.info(repr(value))
		val = {'question':question,'answer':[tuple(value[i:i+3]) for i in range(0, len(value), 3)] ,'content':"list"}
		return val
	else:
		return error


def get_distance(q_noun):
	for idx,i in enumerate(q_noun):
		q_noun[idx] = q_noun[idx].replace(' ','+')
	error = False
	app.logger.info(repr(q_noun))
	loc1 = q_noun[0]
	loc2 = q_noun[1]

	wikidatasearch = wikidata_search([loc1])
	if wikidatasearch['qid']:
		qid1 = wikidatasearch['qid']
		data = wikidata_get_entity(qid1)
		if data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['latitude']:
			latvalue1 = data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['latitude']
			lonvalue1 = data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['longitude']
			app.logger.info(repr(str(latvalue1))+"  "+str(lonvalue1))
		else:
			error = True
	else:
		error = True
			
	wikidatasearch = wikidata_search([loc2])
	if wikidatasearch['qid']:
		qid2 = wikidatasearch['qid']
		data = wikidata_get_entity(qid2)
		if data['entities'][qid2]['claims']['P625'][0]['mainsnak']['datavalue']['value']['latitude']:
			latvalue2 = data['entities'][qid2]['claims']['P625'][0]['mainsnak']['datavalue']['value']['latitude']
			lonvalue2 = data['entities'][qid2]['claims']['P625'][0]['mainsnak']['datavalue']['value']['longitude']
			app.logger.info(repr(str(latvalue2))+"  "+str(lonvalue2))
		else:
			error = True
	else:
		error = True

	if not error:
		# convert decimal degrees to radians 
		lon1, lat1, lon2, lat2 = map(radians, [lonvalue1, latvalue1, lonvalue2, latvalue2])

		# haversine formula 
		dlon = lon2 - lon1 
		dlat = lat2 - lat1 
		a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
		c = 2 * asin(sqrt(a)) 
		r = 6371 # Radius of earth in kilometers. Use 3956 for miles
		d = int(c*r)
		value = str(d) + " kms approx."
		val = {'question':question,'answer':value, 'content' : "string"}
		
		return val
	else:
		return error

def get_date(q_noun):
	app.logger.info(repr(q_noun))
	bkp=[]
	for idx,i in enumerate(q_noun):
		if i == 'number' or i == 'days' or i == 'day' or i == 'time duration':
			continue
		else:
			bkp.append(i)
	q_noun = bkp[:]
	app.logger.info(repr(q_noun))
	
	for idx,i in enumerate(q_noun):
		q_noun[idx] = i.replace('/','-')
	app.logger.info(repr(q_noun))

	date_format = "%d-%m-%Y"
	a = datetime.strptime(q_noun[0], date_format)
	b = datetime.strptime(q_noun[1], date_format)
	delta = b - a
	value = str(delta.days) + " days"
	val = {'question':question,'answer':value, 'content' : "string"}
	return val
def get_description(q_noun):
	val=False
	value=False
	wikidatasearch = wikidata_search(q_noun)
	if wikidatasearch['qid']:
		qid1 = wikidatasearch['qid']
		data = wikidata_get_entity(qid1)
		des = False
		if 'descriptions' in data['entities'][qid1]:
				value = data['entities'][qid1]['descriptions']['en']['value']
				des = True		
		if not des:
			value=searchwiki(q_noun[0])

		if value:
			val = {'question':question,'answer':value , 'content' : "string"}
	return val

def get_property(q_noun):
	ptyl = False
	pty=[]
	b = False
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
	if pty:
		result = {'q_noun':q_noun,'property':pty}
		return result
	else:
		return False

def get_general(q_noun,pty):
	qid = False
	
	wikidatasearch = wikidata_search(q_noun)
	if wikidatasearch:
		qid = wikidatasearch['qid']
		q_noun = wikidatasearch['q_noun']
	else:
		val = False
	if qid:
		data = wikidata_get_entity(qid)

		if 'claims' in data['entities'][qid]:		#checks whether entity has any statements		
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
						
							data2 = wikidata_get_entity("Q"+str(value_id))
							ct+=1
							if data2['success']:
								value = value+""+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
							else:
								return False

						val = {'question':question,'answer':value , 'content' : "string"}
						return val

					elif obj == "string" or obj == "url":			#if property value is string or url
						value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']
						val = {'question':question,'answer':value , 'content' : "string"}
						return val
					
					elif obj == "globe-coordinate":					#if property value is geo coordinates
						latvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['latitude']
						lonvalue = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['longitude']
						value = "latitude: {} longitude: {} ".format(latvalue,lonvalue)
						val = {'question':question,'answer':value , 'content' : "string"}
						return val

					elif obj == "time":
						time = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['time']
						time = time.split('-')
						year = time[0][1:]
						day = time[2][:2]
						month = calendar.month_name[int(time[1])]
						value = "{}th {} {}".format(day,month,year)
						val = {'question':question,'answer':value , 'content' : "string"}
						return val

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
						return val

					elif obj=="monolingualtext":
						value= data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['text']
						val = {'question':question,'answer':value, 'content' : "string"}
						return val


					else:											#for all other property values
						value = data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['amount']
						val = {'question':question,'answer':value , 'content' : "string"}
						return val

		return val

	else:
		answer = searchwiki(key)
		if answer:
			val = {'question':question,'answer':answer, 'content' : "string"}
		else:
			val = {'question':question,'answer':"As of now, the system is unable to answer the question", 'content' : "string"}
		return val
					
def saveqa(question,q_noun,answer,content):
	app.logger.info(repr("in fn"))
	q = History(question,q_noun,answer,content)
	db.session.add(q)
	db.session.commit()

def searchwiki(question):
	
	key = wikipedia.search(question)
	app.logger.info(repr("searching wikipedia for" + str(question)))
	if key:
		try:
			answer = wikipedia.summary(key[0],sentences=1)
		except Exception:
			m = wikipedia.page(wikipedia.search(key[0]))
			answer = wikipedia.summary(m.title,sentences=1)
	else:
		answer = False

	return answer


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050)