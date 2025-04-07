from recorder import speech
from keyword_generator import extract , is_job
from Search_Engine import search  
from Parser import Parse 
from chatbot import chatbot , similarity_score ,similarity_score2
from Summaraizer import split_text_into_chunks,summrize
from speaker import convert
from ans_checker import scoring ,scoring2
from job_wikidata import  job_links     
import numpy as np
import heapq

import time
from flask import Flask, jsonify,request
import os
import csv
from flask_cors import CORS
# Load the data back into a dictionary
# loaded_data = {}
# with open('keywords.csv', 'r') as file:
#     reader = csv.reader(file)
#     for row in reader:
#         key = row[0]
#         # If the value consists of more than one element, convert it to a tuple
#         if len(row) > 2:
#             value = tuple(row[1:])
#         else:
#             value = row[1]
#         loaded_data[key] = value

# # Print the loaded dictionary
# print(loaded_data)

def read_last_row(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            
            rows = list(reader)
            
            last_row = rows[-1]
            
            return last_row            
    return None



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
start_time=time.perf_counter()



KW={}
QA={}
Q={}
TEXTBOOK={}

def aspira(answer):
    #
    #while(timer!=0):
        # timer-=1
        global QA
        global KW 
        global TEXTBOOK
        q ={}
        qa={}

        # text = '''Machine learning teaches computers to recognize patterns and make decisions automatically using data and algorithms.
        # It can be broadly categorized into three types:
        # supervised learning , unsupervised learning and reinforcment learning'''
        # question="what do you know about machine learning?"

        question ="which job would you  prefer?"
        answer="i would like to become an accountant"
        
        if answer==None:
            convert(question)
            text=speech()
        print(scoring(answer))
        print(scoring2(answer))
        # last_row = read_last_row('file/qa.csv')
        if QA:
            question, actual_answer = list(QA.items())[-1]  
            print(question, actual_answer)
        else:
            print("The dictionary is empty")

        

        
        # #text='Not found'
        # while(text == "Not found"):
        #     text=speech() 
        #     if text =="stop":
        #         break
           
        # with open('data.csv', mode='w', newline='', encoding='utf-8') as file:

        keywords=extract(answer)

        # if len(list(words.values)) < 2 and all(x < 8 for x in list(words.values)):
        for  key , score in keywords.items():
            sm=similarity_score(question,key) ##!
            KW[key] = [score,sm]
            KW[key].append(score)

            #value = my_dict.pop('b')
        kw_score=similarity_score2(question,list(keywords.keys()))
        kw={key: (keywords.get(key, None), kw_score.get(key, None)) for key in kw_score}


        first_elements = [v[0] for v in kw.values()]
        second_elements = [v[1] for v in kw.values()]

        first_threshold = sorted(first_elements)[len(first_elements) // 2]  # Middle of first elements
        second_threshold = sorted(second_elements)[len(second_elements) // 2]  # Middle of second elements

        print(f"First threshold: {first_threshold}")
        print(f"Second threshold: {second_threshold}")

        sorted_scores = dict(sorted(KW.items(), key=lambda x: (
        not (x[1][0] <= first_threshold and x[1][1] <= second_threshold), 
            x[1][1],  #the first element
            x[1][0]  #second element
        ), reverse=True))


        for  key , score in sorted_scores.items():
            f_score = (f"{score[0]:.2f}", f"{score[1]:.2f}")

            print(f"{f_score}:{key}")
        KW=sorted_scores
        count1=3
        for  key , score in sorted_scores.items() :
            if not(score[0] >= 1 and len(key.split(' ')) < 4)   :
                return "give a better response"
            else :
                count1 -=1
                if (count1==0):
                    break

                links = job_links(key,no=3) if is_job(key) else search(key,no=2)
                for  no , link in enumerate(links,1):
                    text =Parse(link)
                    if text == 'skip' or text is None:
                        continue
                    # with open(f'file/{no}.txt','w') as file:
                    #     file.writelines(text)
                    # TEXT.append(text)
                    TEXTBOOK[link]=text
                    chunks = split_text_into_chunks(text, max_tokens=200)
                    
                    print(len(chunks))
                    chunks=chunks[:min(len(chunks),5)]
                    count=0
                        
                    # for i in range():
                    #     l=chatbot(chunks[i])
                    #     qa[l]=chunks[i]
                    #     while(count!=3):
                    #         #convert(l)
                    #         count+=1
                    #     score = similarity_score(question, l)
                    #     q[l]=score
                    questions=chatbot(chunks)
                    q_dict=similarity_score2(question,questions)
                    q.update(q_dict)
                    qa.update({question:chunk for question, chunk in zip(questions,chunks)})


                
            

        # sorted_q = dict(sorted(q.items(), key=lambda x: x[1], reverse=True))
        print(q)

        centre_value=1#np.mean(q.values())
        # closest_key = min(q, key=lambda k: abs(q[k] - centre_value))

        closest_key = heapq.nsmallest(3, q.items(), key=lambda item: abs(item[1] - centre_value))[-1][0]

        print('Selected Question')
        print('-'*50)
        print(f"{q[closest_key]:.2f}:{closest_key}")

        question=closest_key
        print(time.perf_counter()-start_time)
        convert(question)
        print(time.perf_counter()-start_time)


        QA[question]=qa[question]
        return question

@app.route('/run-function', methods=['GET'])
def run_function():
    param_value = request.args.get('param', default="default_value") 
    print(param_value) # Get parameter from URL.
    result = aspira(param_value)  

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
# aspira()

