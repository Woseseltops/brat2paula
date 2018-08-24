from os import listdir, mkdir
from shutil import copyfile

class Relation():

	def __init__(self,source_brat_node_id,goal_brat_node_id,relation_name):

		self.source_brat_node_id = source_brat_node_id
		self.goal_brat_node_id = goal_brat_node_id
		self.relation_name = relation_name.replace('2','')

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
	text = open(brat_text_file).read()
	xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_text.dtd">\n<paula version="1.0">\n<header paula_id="'+identifier+'_text" type="text"/>\n<body>'+text+'</body>\n</paula>'
	open(folder+identifier+'.text.xml','w').write(xml)

	#Create token xml
	tokens = [token for token in text.replace('\n',' ').split()]
	xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_mark.dtd">\n<paula version="1.0">\n<header paula_id="'+identifier+'_tok"/>\n<markList type="tok" xml:base="'+identifier+'.text.xml">'

	start_index = 1

	for n,token in enumerate(tokens):

		xml+= '  <mark id="tok_'+str(n)+'" xlink:href="#xpointer(string-range(//body,\'\','+str(start_index)+','+str(len(token))+'))" /><!-- '+token+' -->\n'

		start_index = start_index+ len(token)+ 1

	xml += '</markList>\n</paula>\n'
	open(folder+identifier+'.tok.xml','w').write(xml)

	#Create annoset file xml
	xml = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_struct.dtd">\n<paula version="1.0">\n<header paula_id="'+identifier+'.anno" />\n<structList xmlns:xlink="http://www.w3.org/1999/xlink" type="annoSet">\n<struct id="anno_1">\n  <rel id="rel_1" xlink:href="'+identifier+'.text.xml" />\n  <rel id="rel_2" xlink:href="'+identifier+'.tok.xml" />\n</struct>\n<struct id="anno_2">\n  <rel id="rel_4" xlink:href="'+identifier+'.complements.xml" />\n  <rel id="rel_3" xlink:href="'+identifier+'.complement_heads.xml" />\n</struct>\n<struct id="anno_3">\n  <rel id="rel_5" xlink:href="'+identifier+'.embedding_entities.xml" />\n  </struct>\n<struct id="anno_4">\n  <rel id="rel_6" xlink:href="'+identifier+'.dependencies.xml" />\n<rel id="rel_7" xlink:href="'+identifier+'.dependency_functions.xml" />\n  </struct>\n</structList>\n</paula>\n'
	open(folder+identifier+'.anno.xml','w').write(xml)

	#Process the annotions
	token_index_per_character = []

	for n,token in enumerate(tokens):

		for char in token:
			token_index_per_character.append(n)

		token_index_per_character.append(-1)

	chunk_xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_mark.dtd">\n<paula version="1.1">\n<header paula_id="'+identifier+'_chunks"/>\n<markList xmlns:xlink="http://www.w3.org/1999/xlink" type="chunk" xml:base="'+identifier+'.tok.xml">\n'
	complements_xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_feat.dtd">\n<paula version="1.1">\n<header paula_id="'+identifier+'_complements"/>\n<featList xmlns:xlink="http://www.w3.org/1999/xlink" type="complement" xml:base="'+identifier+'.chunks.xml">\n'
	complement_heads_xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_feat.dtd">\n<paula version="1.1">\n<header paula_id="'+identifier+'_complement_heads"/>\n<featList xmlns:xlink="http://www.w3.org/1999/xlink" type="complement_head" xml:base="'+identifier+'.chunks.xml">\n'
	embedding_entities_xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_feat.dtd">\n<paula version="1.1">\n<header paula_id="'+identifier+'_embedding_entities"/>\n<featList xmlns:xlink="http://www.w3.org/1999/xlink" type="embedding_entity" xml:base="'+identifier+'.chunks.xml">\n'

	chunk_index = 1
	chunk_indices_for_brat_node_ids = {}
	example_text_per_brat_node_id = {}

	relations_between_chunks = []

	for line in open(brat_annotation_file):

		line = line.strip()

		try:
			node_id, annotation, example_text = line.split('\t')
		except ValueError:
			node_id, annotation = line.split('\t')

		#We've encountered a chunk definition
		if 'Complement' in annotation or 'AttitudeEnt ' in annotation or 'SpeechEnt ' in annotation or 'PerceptionEnt ' in annotation or 'Compl-head ' in annotation:
			chunk_indices_for_brat_node_ids[node_id] = chunk_index
			example_text_per_brat_node_id[node_id] = example_text

			#Interpret the character ranges
			raw_char_ranges = [char_range.split() for char_range in annotation.split(';')]
			char_ranges = []
			for raw_char_range in raw_char_ranges:

				if len(raw_char_range) == 3:
					char_ranges.append((int(raw_char_range[1]),int(raw_char_range[2])))
				else:
					char_ranges.append((int(raw_char_range[0]),int(raw_char_range[1])))

			#Link the character ranges to token ids and put that in the xml
			chunk_xml += '<!-- '+example_text+' -->\n <mark id="chunk_'+str(chunk_index)+'" xlink:href="'

			if len(char_ranges) > 1:
				chunk_xml += '('

			for n, (begin_char_index, end_char_index) in enumerate(char_ranges):

				token_indices = set()
				char_index = int(begin_char_index)

				while char_index < int(end_char_index):
					
					if token_index_per_character[char_index] != -1:
						token_indices.add(token_index_per_character[char_index])
		
					char_index += 1

				token_indices = sorted(token_indices)

				if n > 0:
					chunk_xml += ','

				if len(token_indices) == 1:
					chunk_xml += '#tok_'+str(token_indices[0])
				else:
					chunk_xml += '#xpointer(id(\'tok_'+str(token_indices[0])+'\')/range-to(id(\'tok_'+str(token_indices[-1])+'\')))'


			if len(char_ranges) > 1:
				chunk_xml += ')'

			chunk_xml += '"/>\n'

			#Chunk definitions
			if 'AttitudeEnt' in annotation:
				embedding_entities_xml += '<feat xlink:href="#chunk_'+str(chunk_index)+'" value="attitude"/><!-- '+example_text+' -->\n'				
			elif 'SpeechEnt' in annotation:
				embedding_entities_xml += '<feat xlink:href="#chunk_'+str(chunk_index)+'" value="speech"/><!-- '+example_text+' -->\n'				
			elif 'PerceptionEnt' in annotation:
				embedding_entities_xml += '<feat xlink:href="#chunk_'+str(chunk_index)+'" value="perception"/><!-- '+example_text+' -->\n'				
			elif 'Compl-head' in annotation:
				complement_heads_xml += '<feat xlink:href="#chunk_'+str(chunk_index)+'" value="complement_head"/><!-- '+example_text+' -->\n'				

			chunk_index += 1

		#We've encountered an annotation of a chunk defined earlier
		elif 'compl-type' in annotation:

			annotation_type, reference_brat_node_id, value = annotation.split()		
			complements_xml += '<feat xlink:href="#chunk_'+str(chunk_indices_for_brat_node_ids[reference_brat_node_id])+'" value="'+value+'"/><!-- '+str(example_text_per_brat_node_id[reference_brat_node_id])+' -->\n'

		#We've encountered a relation
		elif 'AttitudeEnt:' in annotation or 'SpeechEnt:' in annotation or 'PerceptionEnt:' in annotation:

			goal = None
			second_goal = None

			try:
				source, goal = annotation.split()
			except ValueError:
				try:
					source, goal, second_goal = annotation.split()
				except ValueError:
					pass

			for g in [goal,second_goal]:

				if g != None:

					relation_type = g.split(':')[0]

					source_node_id = source.split(':')[1]
					goal_node_id = g.split(':')[1]
					relations_between_chunks.append(Relation(source_node_id,goal_node_id,relation_type))

		elif 'compl-head ' in annotation:

			desc, source, goal = annotation.split()
			source_node_id = source.split(':')[1]
			goal_node_id = goal.split(':')[1]
			relations_between_chunks.append(Relation(source_node_id,goal_node_id,'head'))


	chunk_xml += '</markList>\n</paula>\n'
	open(folder+identifier+'.chunks.xml','w').write(chunk_xml)

	complement_heads_xml += '</featList>\n</paula>\n'
	open(folder+identifier+'.complement_heads.xml','w').write(complement_heads_xml)

	complements_xml += '</featList>\n</paula>\n'
	open(folder+identifier+'.complements.xml','w').write(complements_xml)

	embedding_entities_xml += '</featList>\n</paula>\n'
	open(folder+identifier+'.embedding_entities.xml','w').write(embedding_entities_xml)

	#Now that all chunks are defined, go through the relations we saved an also turn them to paula xml
	edge_xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_rel.dtd">\n<paula version="1.1">\n<header paula_id="'+identifier+'_dep"/>\n<relList xmlns:xlink="http://www.w3.org/1999/xlink" type="dep" xml:base="'+identifier+'.chunks.xml">\n'
	edge_definition_xml = '<?xml version="1.0" standalone="no"?>\n<!DOCTYPE paula SYSTEM "paula_feat.dtd">\n<paula version="1.1">\n<header paula_id="'+identifier+'_dep_func"/>\n<featList xmlns:xlink="http://www.w3.org/1999/xlink" type="func" xml:base="'+identifier+'.dependencies.xml">\n'

	for n,relation in enumerate(relations_between_chunks):

		try:
			source_id = chunk_indices_for_brat_node_ids[relation.source_brat_node_id]
			goal_id = chunk_indices_for_brat_node_ids[relation.goal_brat_node_id]
		except KeyError:
			continue

		edge_xml += '<rel id="rel_'+str(n)+'" xlink:href="#chunk_'+str(source_id)+'" target="#chunk_'+str(goal_id)+'"/>\n'
		edge_definition_xml += '<feat xlink:href="#rel_'+str(n)+'" value="'+relation.relation_name+'"/>\n'

	edge_xml += '</relList>\n</paula>\n'
	open(folder+''+identifier+'.dependencies.xml','w').write(edge_xml)

	edge_definition_xml += '</featList>\n</paula>\n'
	open(folder+''+identifier+'.dependency_functions.xml','w').write(edge_definition_xml)

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

		print('converting',filename)
		brat2paula(INPUT_FOLDER+filename,INPUT_FOLDER+identifier+'.ann',
					identifier,DTD_FOLDER,OUTPUT_FOLDER)