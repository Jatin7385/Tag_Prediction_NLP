from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import math
import torch
import wikipedia
from newspaper import Article, ArticleException
from GoogleNews import GoogleNews
import IPython
from pyvis.network import Network
import json
from neo4j import GraphDatabase
from Neo4j_KG_Maker import KG
import csv


# Database Credentials
uri             = "bolt://54.237.204.100:7687"
userName        = "neo4j"
password        = "grid-workings-admiralties"

# Entities list :
entities = []

# Relations list
final_relations = []

# Connect to the neo4j database server
graphDB_Driver  = GraphDatabase.driver(uri, auth=(userName, password))


# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

def neo4j_work():
    pass

def extract_relations_from_model_output(text):
    relations = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    text_replaced = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "")
    for token in text_replaced.split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        relations.append({
            'head': subject.strip(),
            'type': relation.strip(),
            'tail': object_.strip()
        })
    return relations

def are_relations_equal(r1, r2):
        return all(r1[attr] == r2[attr] for attr in ["head", "type", "tail"])
def exists_relation(r1):
    return any(are_relations_equal(r1, r2) for r2 in final_relations)
def add_relation(r):
    if not exists_relation(r):
        final_relations.append(r)
def print_relations():
    print("Relations:")
    for r in final_relations:
        entities.append(r["head"])
        entities.append(r["tail"])
        print(f"  {r}")
    return entities
def from_small_text_to_kb(text, verbose=False):
    # kb = KB()

    # Tokenizer text
    model_inputs = tokenizer(text, max_length=512, padding=True, truncation=True,
                            return_tensors='pt')
    if verbose:
        print(f"Num tokens: {len(model_inputs['input_ids'][0])}")

    # Generate
    gen_kwargs = {
        "max_length": 216,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": 3
    }
    generated_tokens = model.generate(
        **model_inputs,
        **gen_kwargs,
    )
    decoded_preds = tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

    # create kb
    for sentence_pred in decoded_preds:
        relations = extract_relations_from_model_output(sentence_pred)
        for r in relations:
            add_relation(r)

    return final_relations


# Open JSON File : 
file = open('space_race_q.json')

# Return JSON Object as a dictionary]

data = json.load(file)


print("Dataset title : " , data['title'])
print("Number of qas, context sets : " , len(data["paragraphs"]))

qas_list = data["paragraphs"]
# To get the particular set of qas with context : 

# print("QAS Set are as follows : ")
# for i in range(len(qas_list)):
#     print(qas_list[i])
questions_answers_list = data['paragraphs'][0]["qas"]
# print(questions_answers_list)
# print(data['paragraphs'][0]["qas"])
context = data['paragraphs'][0]["context"]

# print("Context : ", context)
# print("Relations : ")
# kb = from_small_text_to_kb(context, verbose=True)

# # entities = list(set(entities))
# entities = print_relations()
# entities = list(set(entities))
# print(entities)
# # for i in range(len(final_relations)):
# #     print(final_relations[i])

# # CQL to create a entities in the KG
# cqlCommands = []
# for i in range(len(entities)):
#     name_entity = entities[i].replace(' ', '_')
#     name_entity = name_entity.replace(',', '')
#     type_entity = "Entity" # We need to change this according to the NER from Spacy
#     cqlCreate = f"CREATE ({name_entity} : {type_entity}) SET {name_entity}.name = $name,{name_entity}  \n"
#     cqlCommands.append(cqlCreate)
#     print(cqlCreate)

# cqlCommands.append("*** \n")

# for i in range(len(final_relations)):
#     rel = final_relations[i]
#     head = rel["head"].replace(' ', '_')
#     head = head.replace(',', '')
#     type_ = rel["type"].replace(' ', '_')
#     type_ = type_.replace(',', '')
#     tail = rel["tail"].replace(' ','_')
#     tail = tail.replace(',','')
#     cqlRelation = f"MATCH ({head} : Entity) , ({tail} : Entity) WHERE {head}.name = '{head}' AND {tail}.name = '{tail}' CREATE ({head}) -[:{type_}]->({tail}) \n"
#     cqlCommands.append(cqlRelation)
#     # print(rel)
#     print(cqlRelation)

# print(cqlCommands)

# # Writing the commands to a text file : 
# file1 = open("commands.txt","w")
# file1.writelines(cqlCommands)
# file1.close()

# # Now lets make the Knowledge Graph : 
# kg = KG("bolt://44.203.229.74:7687", "neo4j", "thermometer-sponges-basins")
# kg.create_graph()
# kg.close()

## Extracting the questions present in the dataset : 
questions = []
for i in range(len(questions_answers_list)):
    question = questions_answers_list[i]["question"]
    questions.append(question)

print("Context : ", context)
print("Relations : ")
kb = from_small_text_to_kb(context, verbose=True)

entities1 = []
final_final_relations = []
# Writing the question relations/entities to a text file : 
with open("question_relations.csv", mode = "w") as file:
    # Write the relations to the file : 
    csvwriter = csv.writer(file)
    # Named entity recognition and relationship extraction of the questions present : 
    for i in range(len(questions)):
        final_relations = []
        entity = []
        file_list = []
        kb = from_small_text_to_kb(questions[i], verbose=True)
        # entities = list(set(entities))
        entities = print_relations()
        print("Entity : ", entity)
        entities = list(set(entity))
        entities1.append(entities)
        for j in range(len(final_relations)):
            file_list = []
            head = final_relations[j]['head']
            head = head.replace(",","")
            head = head.replace(" ","_")
            type_ = final_relations[j]['type']
            type_ = type_.replace(",","")
            type_ = type_.replace(" ","_")
            tail = final_relations[j]['tail']
            tail = tail.replace(",","")
            tail = tail.replace(" ","_")
            file_list.append(head)
            file_list.append(type_)
            file_list.append(tail)
            csvwriter.writerow(file_list)
        final_final_relations.append(final_relations)

    print(entities)
    print(final_final_relations)

