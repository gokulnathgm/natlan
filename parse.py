import nltk
w = nltk.word_tokenize("which is the highest point in india")
t = nltk.pos_tag(w)
grammar = "NP: {<JJ.*>*<NN.*>+}"
np_parser = nltk.RegexpParser(grammar)
np_tree = np_parser.parse(t)
q_noun = []
for i in np_tree:
   	NPs=""
   	if str(type(i))=="<class 'nltk.tree.Tree'>":
   		for k in i:
   			if NPs=="":
				NPs=k[0]
   			else:
   				NPs=NPs+"+"+k[0]
   		q_noun.append(NPs)
print q_noun
