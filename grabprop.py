from app import app
from models import db
import json
import urllib2
import json


from app import Properties
from models import db

with app.app_context():
	response1 = urllib2.urlopen('https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q668&format=json&languages=en')
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
				db.session.commit()


	