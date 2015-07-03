from app import app
from models import db
import urllib2
import json
db.init_app(app)

with app.app_context():
	from app import Properties,History
	"""db.drop_all()"""
	db.create_all()

	"""response1 = urllib2.urlopen('https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q668&format=json&languages=en')
	data = json.load(response1)   

	for entity in data['entities'].keys():
		for pid in data['entities'][entity]['claims'].keys():
			ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+pid+"&format=json&languages=en"
			print ur
			response2 = urllib2.urlopen(ur)

		data2 = json.load(response2)
		for ent in data2['entities']:
			label = data2['entities'][ent]['labels']['en']['value']
			print label
			p = Properties(label, pid)
			db.session.add(p)
			db.session.commit()"""

    

	"""with open('properties-en.json') as data_file:
		data = json.load(data_file)
		for ent in data['properties']:
			label = data['properties'][ent]
			p = Properties(label, ent, "")
			db.session.add(p)
		db.session.commit()


	ptys = Properties.query.all()
	for pty in ptys:
		ur = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+pty.pid+"&format=json&languages=en"
		response = urllib2.urlopen(ur)

		data = json.load(response)
		print pty.pid
		if 'aliases' in data['entities'][pty.pid]:
			aliases = ""
			for alias in data['entities'][pty.pid]['aliases']['en']:
				aliases = aliases + "|" + alias['value']
			pty.aliases = aliases
			print pty.pid
			print pty.aliases
	db.session.commit()

"""