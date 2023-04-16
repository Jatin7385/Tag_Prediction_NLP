from neo4j import GraphDatabase
import csv

class KG:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.flag = 0

    def close(self):
        self.driver.close()

    def create_graph(self):
        with self.driver.session() as tx:
            # Reading the commands from a text file : 
            file1 = open("./commands.txt","r+")
            lines = file1.readlines()
            flag = 0
            print(lines)
            for i in range(len(lines)): 
                lines[i] = lines[i].replace(" \n","")
                print(lines[i])
                if(lines[i] == "***"):
                    flag = 1
                    print("Hello")
                    continue
                if(flag == 0):
                    x = lines[i].split(",")
                    msg = x[1].strip()
                    com = x[0]
                    print(x[1])
                    result = tx.run(com,name = msg)
                    print(result)
                else:
                    result = tx.run(lines[i])
                    print(result)
            file1.close()
    def extract_subgraphs(self):
        question_relations = []

        with open('question_relations.csv',mode = "r") as file:
            csvFile = csv.reader(file)
            
            for lines in csvFile:
                if(len(lines) == 0):continue
                print(lines)
                question_relations.append(lines)

        