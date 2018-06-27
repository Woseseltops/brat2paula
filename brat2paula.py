from os import listdir, mkdir
from shutil import copyfile

def brat2paula(brat_text_file,brat_annotation_file,identifier,dtd_folder,output_folder):

	folder = output_folder+identifier+'/'

	#Create the new folder for this doc
	try:
		mkdir(folder)
	except FileExistsError:
		pass

	#Copy over the static dtds
	for dtd in listdir(dtd_folder):
		copyfile(dtd_folder+dtd,folder+dtd)

	#Create text xml
	text = open(brat_text_file).read().replace('ROOT ','')
	xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_text.dtd">\n<paula version="1.0">\n<header paula_id="'+identifier+'_text" type="text"/>\n<body>'+text+'</body>\n</paula>'
	open(folder+identifier+'.text.xml','w').write(xml)

	#Create token xml
	tokens = [token for token in text.replace('\n',' ').split() if token != 'ROOT']
	xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_mark.dtd">\n<paula version="1.0">\n<header paula_id="'+identifier+'_tok"/>\n<markList type="tok" xml:base="'+identifier+'.text.xml">'

	start_index = 1

	for n,token in enumerate(tokens):

		xml+= '  <mark id="tok_'+str(n)+'" xlink:href="#xpointer(string-range(//body,\'\','+str(start_index)+','+str(len(token))+'))" /><!-- '+token+' -->\n'

		start_index = start_index+ len(token)+ 1

	xml += '</markList>\n</paula>\n'
	open(folder+identifier+'.tok.xml','w').write(xml)

	#Create annoset file xml
	xml = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_struct.dtd">\n<paula version="1.0">\n<header paula_id="'+identifier+'.anno" />\n<structList xmlns:xlink="http://www.w3.org/1999/xlink" type="annoSet">\n<struct id="anno_1">\n  <rel id="rel_1" xlink:href="'+identifier+'.text.xml" />\n  <rel id="rel_2" xlink:href="'+identifier+'.tok.xml" />\n</struct>\n</structList>\n</paula>\n'
	open(folder+identifier+'.anno.xml','w').write(xml)

	#Process the annations
	token_index_per_character = []

	for n,token in enumerate(tokens):

		for char in token:
			token_index_per_character.append(n)

		token_index_per_character.append(-1)

	print(token_index_per_character)

	for line in open(brat_annotation_file):

		line = line.strip()

		try:
			node_id, annotation, example_text = line.split('\t')
		except ValueError:
			node_id, annotation = line.split('\t')

		if 'Complement' in annotation:
			annotation_type, begin_char_index, end_char_index = annotation.split()
			token_index = token_index_per_character[int(begin_char_index)]
			print(annotation,example_text,tokens[token_index])

def prettify_xml(xml):
	from lxml import etree
	return etree.tostring(etree.fromstring(xml),pretty_print=True)

if __name__ == '__main__':
	ROOT = '/vol/tensusers/wstoop/perspective/brat2paula/'
	INPUT_FOLDER = ROOT+'input/'
	OUTPUT_FOLDER = ROOT+'thucydides/'
	DTD_FOLDER = ROOT+'dtds/'

	for filename in listdir(INPUT_FOLDER):

		if '.ann' in filename:
			continue

		identifier = filename.replace('.txt','')

		brat2paula(INPUT_FOLDER+filename,INPUT_FOLDER+identifier+'.ann',
					identifier,DTD_FOLDER,OUTPUT_FOLDER)