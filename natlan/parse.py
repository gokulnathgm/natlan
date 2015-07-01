import nltk,pattern.en
s = raw_input("String???   ")

t=pattern.en.tag(s)
grammar = r"""NP: {<JJ.*>+<NN.*>+}
					{<NN.*>+<IN>*<JJ.*>*}"""					#grammar for chunking
np_parser = nltk.RegexpParser(grammar)
np_tree = np_parser.parse(t)
q_noun = []

for i in np_tree:								#to get all the Noun Phrases to q_noun
   	NPs=""
   	if str(type(i))=="<class 'nltk.tree.Tree'>":		
   		for k in i:
   			if NPs=="":
   				NPs=k[0]
   			else:
   				NPs=NPs+" "+k[0]

		q_noun.append(NPs)
print q_noun

conjuction = ["of","in","as","if","as if","even","than","that","until","and","but","or","nor","for","yet","so"]
for idx,i in enumerate(q_noun):					#add + in btwn words for searching
	for j in conjuction:
		q_noun[idx]=str(q_noun[idx]).replace(j+" "," ")
		q_noun[idx]=str(q_noun[idx]).replace(" "+j,"")
print q_noun