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

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		history = History.query.order_by(History.id.desc()).limit(9)
		return render_template('index.html',page="home",history=history)
	elif request.method == 'POST':
		history = History.query.order_by(History.id.desc()).limit(5)
		des = False
		grammar1=False
		grammar2=False
		
		app.logger.info(repr(request.form))
		question = request.form['question']
		question = question.replace('?','')
		#q_tagged = pattern.en.tag(question)				#tags the question
		blob = TextBlob(question)
		q_tagged = blob.tags
		app.logger.info(repr(q_tagged))


		#grammar for list all type questions
		grammar=r"""NP: {<JJ.*>*<NNS><IN>+<DT>*<NN.*>+}"""
		np_parser=nltk.RegexpParser(grammar)
		np_tree = np_parser.parse(q_tagged)
		app.logger.info(repr(np_tree))
		q_noun = []
		for i in np_tree:
			NPs=""
			if str(type(i))=="<class 'nltk.tree.Tree'>":
				grammar2=True
				for k in i:
				
					if k[1]=="NNS":
						t=pattern.en.singularize(k[0])
					else:
						t=k[0]
					if NPs=="":
						NPs=t
					else:
						NPs=NPs+" "+t
					
				q_noun.append(NPs)



			app.logger.info(repr(q_noun))
		if not q_noun:

			grammar = r"""NP: {<JJ.*>*<IN>*<NN.*>+}
						{<NN.*><IN>+<JJ.*>+}
						{<IN>*<CD>+}"""	
										#grammar for chunking
			np_parser = nltk.RegexpParser(grammar)
			np_tree = np_parser.parse(q_tagged)

			q_noun = []
			app.logger.info(repr(np_tree))
			for i in np_tree:								#to get all the Noun Phrases to q_noun
	   			NPs=""
	   			if str(type(i))=="<class 'nltk.tree.Tree'>":
	   				grammar1=True		
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


		if len(q_noun) == 1 and grammar1==True:
			q_noun1=q_noun[:]
			app.logger.info(repr(q_noun1))
			q_noun=[]
			grammar=r"""NP:{<JJ.*>*<NN.*>+<VB.*><IN>?}"""  #grammar for indirect type questions
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
   				qid = False
   				for idx,i in enumerate(q_noun):					#add + in btwn words for searching
					app.logger.info(repr(str(q_noun[idx])))
					x=str(q_noun[idx]).replace(" ","+")
					q_noun[idx]=x
				for i in q_noun:			
					ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
					app.logger.info(repr(ur))
					response = urllib2.urlopen(ur)
					data = json.load(response)
					app.logger.info(repr(i))
					


				#pty=Properties.query.filter(Properties.pid == "P31").all()
		
   		
   		app.logger.info(repr(q_noun))

   		rng = False
   		dt = False
   		for k in q_noun:
   			if 'distance' in k or 'length' in k or 'long' in k or 'kilometers'in k or 'how far' in question:
   				rng = True
   				app.logger.info(repr("range query"))
   				break

   		if ('days' in question and 'between' in question) or ('time' in question and 'duration' in question) :
   			dt = True


		noun_save = ""
		for a in q_noun:
			noun_save += " | " + a.lower()
		
		app.logger.info(repr(history))

		ques = History.query.filter_by(q_noun = noun_save).first()
		if ques:
			value = {'question':question,'answer':ques.answer, 'content' : ques.content}
			flash(value,'success')
			return render_template('index.html',page="home",history=history)

		if rng == False and dt == False:

			if not q_noun:
				question = question.replace(' ','+')
				ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+question+"&format=json&language=en"
				app.logger.info(repr(ur))
				response = urllib2.urlopen(ur)
				data = json.load(response)

				if data['search']:
					if 'id' in data['search'][0]:
						qid = data['search'][0]['id']
						ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
						app.logger.info(repr(ur))
						response = urllib2.urlopen(ur)
						data = json.load(response)
					
						if 'description' in data['entities'][qid]:
							app.logger.info(repr(qid))
							value = data['entities'][qid]['description']['en']['value']
							answer=""
							if value:
								if value == "Wikipedia disambiguation page" or value == "Wikimedia disambiguation page":
									answer = searchwiki(question,value)
							else:
								#answer = searchwiki(question,"")
								answer = value
						if 'descriptions' in data['entities'][qid]:
							app.logger.info(repr(qid))
							value = data['entities'][qid]['descriptions']['en']['value']
							app.logger.info(repr(value))
							answer=""
							
							if value == "Wikipedia disambiguation page" or value == "Wikimedia disambiguation page":
								answer = searchwiki(question,value)
							else:
								#answer = searchwiki(question,"")
								answer = value
						else:
							answer=searchwiki(question,"string")
					#else:
						#answer = searchwiki(question,'string')
					val = {'question':question.replace('+',' '),'answer':answer, 'content' : "string"}								#property doesnt exist if pid is empty
					flash(val,'success')
					return render_template('index.html',page="home",history=history)
				"""else:
					val = {'question':question,'answer':"As of now, the system is unable to answer this question...", 'content' : "string"}
					flash(val,'warning')
					return render_template('index.html',page="home",history=history)"""


			

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
								

				if not pty and grammar2==False:	
					app.logger.info(repr(key))
					answer = searchwiki(question,"")
					val = {'question':question.replace('+',' '),'answer':answer, 'content' : "string"}								#property doesnt exist if pid is empty
					flash(val,'success')
					return render_template('index.html',page="home",history=history)


			if not q_noun:									#no entries to search
				val = {'question':question,'answer':"As of now, the system is unable to answer this question...", 'content' : "string"}
				flash(val,'warning')
				return render_template('index.html',page="home",history=history)

			
			for idx,i in enumerate(q_noun):					#add + in btwn words for searching
				app.logger.info(repr(str(q_noun[idx])))
				x=str(q_noun[idx]).replace(" ","+")
				q_noun[idx]=x
				

			app.logger.info(repr(q_noun))


			"""finds Entity id (Qid) for elements in q_noun, searches till atleast one result is obtained"""
			if grammar2==True:
				gr = False

				qid = False
				for i in q_noun:			
					ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
					app.logger.info(repr(ur))
					response = urllib2.urlopen(ur)
					data = json.load(response)
					app.logger.info(repr(i))
					if data['search']:
						app.logger.info(repr(data))
						if 'description' in data['search'][0]:
							if data['search'][0]['description'] == 'Wikipedia disambiguation page' or data['search'][0]['description'] == 'Wikimedia disambiguation page':
								qid = data['search'][1]['id']
							else:
								qid = data['search'][0]['id']
						else:
							qid = data['search'][0]['id']
						app.logger.info(repr("Qid  : "+qid))
						break
				if qid:
					ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
					response = urllib2.urlopen(ur)
					data = json.load(response)
					
					qid1=qid[1:]
					qid=qid1[:]
					app.logger.info(repr(qid))
					ur="https://wdq.wmflabs.org/api?q=claim[39:"+qid+"]"
					app.logger.info(repr(ur))
					response = urllib2.urlopen(ur)
					data = json.load(response)
					value=""
					ct=0
					if data['status']['items']!=0:
						gr=True
						for i in range(len(data['items'])):	
									#gets value from property page
							if ct>0:
								value=value+", "		
							value_id = data['items'][i]
							app.logger.info(repr(value_id))
												
							u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
							response1 = urllib2.urlopen(u)
							data2 = json.load(response1)
							ct+=1
							if data2['success']:
								if 'labels' in data2['entities']['Q'+str(value_id)]:
									value = value+""+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
								else:
									continue
							else:
								val = {'question':question,'answer':"As of now, the system is unable to answer this question...", 'content' : "string"}
								flash(val,'warning')
								return render_template('index.html',page="home",history=history)


					else:
						ur="https://wdq.wmflabs.org/api?q=claim[31:"+qid+"]"
						app.logger.info(repr(ur))
						response = urllib2.urlopen(ur)
						data = json.load(response)
						value=""
						ct=0
						if data['status']['items']!=0:
							gr=True
							for i in range(len(data['items'])):	
								#gets value from property page
								if ct>0:
									value=value+", "		
								value_id = data['items'][i]
								app.logger.info(repr(value_id))
													
								u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
								response1 = urllib2.urlopen(u)
								data2 = json.load(response1)
								ct+=1
								if data2['success']:
									if 'labels' in data2['entities']['Q'+str(value_id)]:
										value = value+""+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
									else:
										continue
						else:
							gr=False

				elif not qid or gr==False:
				
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
							q_noun.append(NPs)
					ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+NPs+"&format=json&language=en"
					app.logger.info(repr(ur))
					response = urllib2.urlopen(ur)
					data = json.load(response)
					app.logger.info(repr(NPs))
					if data['search']:
						app.logger.info(repr(data))
						qid = data['search'][0]['id']
						app.logger.info(repr("Qid  : "+qid))

					ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+nou+"&format=json&language=en"
					app.logger.info(repr(ur))
					response = urllib2.urlopen(ur)
					data = json.load(response)
					app.logger.info(repr(nou))
					if data['search']:
						app.logger.info(repr(data))
						qid1 = data['search'][0]['id']
						app.logger.info(repr("Qid  : "+qid1))
						ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid1+"&format=json&languages=en"
						response = urllib2.urlopen(ur)
						data = json.load(response)
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
									u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
									response1 = urllib2.urlopen(u)
									data2 = json.load(response1)
									if data2['success']:
										value = data2['entities']['Q'+str(value_id)]['labels']['en']['value']
										ptyl = Properties.query.filter(Properties.label.like("%"+value+"%")).all()		#searches in label
										if not ptyl:
											ptyl = Properties.query.filter(Properties.aliases.like("%"+value+"%")).all()		#search in aliases

										if ptyl:
											for k in range(len(ptyl)):											#Strict comparison if >1 ptys found
												if ptyl[k].label.lower() == value.lower():#or value.lower() in ptyl[k].aliases.lower():
													pty = ptyl[k]
													b=True
													app.logger.info(repr(value))
													break
											if not b:
												continue
											app.logger.info(repr(pty))
											app.logger.info(repr("pty found"))
											
											pid = pty.pid
											app.logger.info(repr("Pid  : "+pid))
											ur="https://wdq.wmflabs.org/api?q=claim[31:"+qid[1:]+"]%20and%20claim["+pid[1:]+":"+qid1[1:]+"]"
											app.logger.info(repr(ur))
											response = urllib2.urlopen(ur)
											data = json.load(response)
											value=""
											ct=0
											if data['status']['items']!=0:
												gr=True
													
												for i in range(len(data['items'])):	
													#gets value from property page
													if ct>0:
														value=value+", "		
													value_id = data['items'][i]
													app.logger.info(repr(value_id))
																
													u = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+"Q"+str(value_id)+"&format=json&languages=en"
													response1 = urllib2.urlopen(u)
													data2 = json.load(response1)
													ct+=1
													if data2['success']:
														if 'labels' in data2['entities']['Q'+str(value_id)]:
															value = value+""+data2['entities']['Q'+str(value_id)]['labels']['en']['value']
														else:
															continue

														"""else:
															val = {'question':question,'answer':"As of now, the system is unable to answer this question...", 'content' : "string"}
															flash(val,'warning')
															return render_template('index.html',page="home",history=history)"""
													
											else:
												continue
											
									else:
										continue
					if gr==True:
						val = {'question':question,'answer':value ,'content':"string"}
						flash(val,'success')
						saveqa(question,noun_save,value,"string")
						return render_template('index.html',page="home",history=history)



				

					"""find entity using qid"""

				if gr==False:
					value = searchwiki(key,'string')
				
				val = {'question':question,'answer':value ,'content':"string"}
				flash(val,'success')
				saveqa(question,noun_save,value,"string")
				return render_template('index.html',page="home",history=history)
			app.logger.info(repr(des))
			if des == True:
				if data['search']:
					if 'description' in data['search'][0]:
						value = data['search'][0]['description']
						if value == "Wikipedia disambiguation page" or value == "Wikimedia disambiguation page":
							value = searchwiki(key,value)
						"""else:
							qid = data['search'][0]['id']
							ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
							app.logger.info(repr(ur))
							response = urllib2.urlopen(ur)
							data = json.load(response)
					
							if 'description' in data['entities'][qid]:
								answer = data['entities'][qid]['description']['en']['value']
								answer=""
								if value:
									if value == "Wikipedia disambiguation page" or value == "Wikimedia disambiguation page":
										answer = searchwiki(question,value)
								else:
									#answer = searchwiki(question,"")
									answer = value
							else:
								answer=searchwiki(question,"string")"""

					else:
						app.logger.info(repr(key))
						value=searchwiki(key,"string")

				else:
					value=searchwiki(key,"string")
					


				val = {'question':question,'answer':value , 'content' : "string"}
				flash(val,'success')
				saveqa(question,noun_save,value,"string")
				return render_template('index.html',page="home",history=history)

			elif not grammar2:
				qid = False
				for i in q_noun:			
					ur = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+i+"&format=json&language=en"
					app.logger.info(repr(ur))
					response = urllib2.urlopen(ur)
					data = json.load(response)
					app.logger.info(repr(i))
					if data['search']:
						app.logger.info(repr(data))
						if 'description' in data['search'][0]:
							if data['search'][0]['description'] == 'Wikipedia disambiguation page' or data['search'][0]['description'] == 'Wikimedia disambiguation page':
								qid = data['search'][1]['id']
							else:
								qid = data['search'][0]['id']
						else:
							qid = data['search'][0]['id']
						app.logger.info(repr("Qid  : "+qid))
						break
				if qid:
					ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid+"&format=json&languages=en"
					response = urllib2.urlopen(ur)
					data = json.load(response)
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
											val = {'question':question,'answer':"As of now, the system is unable to answer this question...", 'content' : "string"}
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

									val= {'question':question,'answer':"As of now, the system is unable to answer this question...", 'content' : "string"}
									flash(val,'warning')
									return render_template('index.html',page="home",history=history)
								elif obj=="monolingualtext":
									value= data['entities'][qid]['claims'][pid][0]['mainsnak']['datavalue']['value']['text']
									val = {'question':question,'answer':value, 'content' : "string"}
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
					flash(val,'success')
					return render_template('index.html',page="home",history=history)

				else:
					answer = searchwiki(key,"")
					val = {'question':question,'answer':answer, 'content' : "string"}
					flash(val,'success')
					return render_template('index.html',page="home",history=history)

		if rng == True:
			app.logger.info(repr(q_noun))
			for idx,k in enumerate(q_noun):
				if 'distance' in k or 'length' in k or 'long' in k or 'kilometers'in k:
					del q_noun[idx]

			for idx,i in enumerate(q_noun):
				q_noun[idx] = q_noun[idx].replace(' ','+')

			app.logger.info(repr(q_noun))

			loc1 = q_noun[0]
			loc2 = q_noun[1]

			ur1 = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+loc1+"&format=json&language=en"
			response1 = urllib2.urlopen(ur1)
			data1 = json.load(response1)
			if 'description' in data1['search'][0]:
				if data1['search'][0]['description'] == "Wikimedia disambiguation page" or data1['search'][0]['description'] == "Wikipedia disambiguation page":
					qid1 = data1['search'][1]['id']
				else:
					qid1 = data1['search'][0]['id']
			else:
				qid1 = data1['search'][0]['id']
			ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid1+"&format=json&language=en"
			response = urllib2.urlopen(ur)
			data = json.load(response)
			latvalue1 = data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['latitude']
			lonvalue1 = data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['longitude']
			app.logger.info(repr(str(latvalue1))+"  "+str(lonvalue1))
			ur1 = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+loc2+"&format=json&language=en"
			response1 = urllib2.urlopen(ur1)
			data1 = json.load(response1)
			if 'description' in data1['search'][0]:
				if data1['search'][0]['description'] == "Wikimedia disambiguation page" or data1['search'][0]['description'] == "Wikipedia disambiguation page":
					qid1 = data1['search'][1]['id']
				else:
					qid1 = data1['search'][0]['id']
			else:
				qid1 = data1['search'][0]['id']
			ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+qid1+"&format=json&language=en"
			response = urllib2.urlopen(ur)
			data = json.load(response)
			latvalue2 = data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['latitude']
			lonvalue2 = data['entities'][qid1]['claims']['P625'][0]['mainsnak']['datavalue']['value']['longitude']
			app.logger.info(repr(str(latvalue2))+"  "+str(lonvalue2))
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
			flash(val,'success')
			saveqa(question,noun_save,value,"string")
			return render_template('index.html',page="home",history=history)

		if dt == True:
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
			flash(val,'success')
			saveqa(question,noun_save,value,"string")
			return render_template('index.html',page="home",history=history)



def saveqa(question,q_noun,answer,content):
	app.logger.info(repr("in fn"))
	q = History(question,q_noun,answer,content)
	db.session.add(q)
	db.session.commit()

def searchwiki(question,value):
<<<<<<< HEAD
	app.logger.info(repr("search wiki fn"))
=======
	app.logger.info(repr("search wikipedia"))
>>>>>>> 47f0ab6e543a02ecc01afa9d33e45b1866593b6e
	key = wikipedia.search(question)
	app.logger.info(repr(question))
	if value=="Wikipedia disambiguation page" or value=="Wikimedia disambiguation page":
		m = wikipedia.page(wikipedia.search(key[0]))
		answer = wikipedia.summary(m.title,sentences=1)
	else:
		answer = wikipedia.summary(key[0],sentences=1)
	return answer



if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050)
