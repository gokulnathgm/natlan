import re
import nltk

strn = raw_input("Ask Something\n")

tok = nltk.word_tokenize(strn)
tup = nltk.pos_tag(tok)
noun=[]

for i in tup:
	if i[1]=='NN' or i[1]=='NNP' or i[1]=='NNPS' or i[1]=='NNS':
		noun.append(i[0])

print noun
