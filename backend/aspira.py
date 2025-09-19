from B_recorder import speech
from C_ans_checker import scoring ,scoring2
from D_keyword_generator import keyword_extraction, is_job
from E_job_wikidata import  job_links     
from F_Search_Engine import search  
from G_Parser import Parse 
from H_Summaraizer import split_text_into_chunks,textrank
from I_chatbot import chatbot ,similarity_score
from J_speaker import convert
import numpy as np
import heapq
import logging
import time
from flask import Flask, jsonify,request
from flask_bcrypt import Bcrypt
from db import users_collection

from flask_cors import CORS

import logging

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('log/aspira.log')
if not logger.hasHandlers():
    logger.addHandler(file_handler)


app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
# CORS(app)

start_time=time.perf_counter()


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









KW={}
QA={}
Q={}
TEXTBOOK={}

def aspira(answer="i would like to become an accountant"):
#   timer =3

#   while(timer!=0):
#     timer-=1
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
    
    if answer==None:
        convert(question)
        text=speech()
    
    logger.info(f"scoring(answer): {scoring(answer)}")
    logger.info(f"scoring2(answer): {scoring2(answer)}")
    # last_row = read_last_row('file/qa.csv')

    if QA:
        question, answer = list(QA.items())[-1]  
        logger.info(question, answer)
    else:
        logger.info("The dictionary is empty")

    #Divide old values by 2 to reduce there relevancy
    if KW:
        KW = {key: (a/2,b/2) for key,(a,b) in KW.items()}
    else:
        KW={}


    
    # #text='Not found'
    # while(text == "Not found"):
    #     text=speech() 
    #     if text =="stop":
    #         break
        
    # with open('data.csv', mode='w', newline='', encoding='utf-8') as file:

    keywords=keyword_extraction(answer)
    keywords = dict(sorted(keywords.items(), key=lambda item: item[1]))

        # if len(list(words.values)) < 2 and all(x < 8 for x in list(words.values)):
    keys = list(keywords.keys())
    scores = list(keywords.values())

    sims = similarity_score(question, keys) 
    print(KW)
    print(keys)
    print(scores)
    for key, score in zip(keys, scores):
        sm = sims[key]
        if key in KW:
            KW[key][0] += score
            print('key',key)
            print('KW,',KW)
            KW[key][1] += sm
        else:
            KW[key] = [score, sm]

    sorted_scores = dict(sorted(
    KW.items(),
    key=lambda x: np.sqrt(x[1][0] * x[1][1]),
    reverse=True
    ))

    KW=sorted_scores

    logger.info("\n" + "\n".join(f"({score[0]:.2f}, {score[1]:.2f}):{key}" for key, score in KW.items()))

    
    count1=3
    for  key , score in sorted_scores.items() :
        if not(score[0] >= 0.1 and len(key.split(' ')) < 4)   :
            logger.debug(f"skipped ,{key}")
            continue
        else :
            count1 -=1
            if (count1==0):
                break

            # links = job_links(key,no=3) if is_job(key) else search(key,no=3)
            corpus=[]
            links = search(key,no=3,items=['interview questions','questions for interviews']) if is_job(key) else search(key,no=3)
            for  no , link in enumerate(links,1):
                # print('ok')
                text =Parse(link)
                # print('ok')
                if text == 'skip' or text is None:
                    continue

                TEXTBOOK[link]=text
                corpus_dict=textrank(text)
                corpus.extend(list(corpus_dict.keys()))
                logger.info(len(corpus_dict))

                # chunks.extend(split_text_into_chunks(text, max_tokens=200))
                print('ok')
            logger.info(len(corpus))
            # chunks_dict=similarity_score(key,chunks)            

            chunks=split_text_into_chunks('.'.join(corpus))
            # print(chunks)
            questions=chatbot(chunks)
            q_dict=similarity_score(question,questions)
            q.update(q_dict)
            qa.update({question:chunk for question, chunk in zip(questions,chunks)})

    # sorted_q = dict(sorted(q.items(), key=lambda x: x[1], reverse=True))
    print(q)

    # centre_value=np.mean(q.values())
    centre_value = np.mean(list(q.values()))

    # closest_key = min(q, key=lambda k: abs(q[k] - centre_value))

    closest_key = heapq.nsmallest(3, q.items(), key=lambda item: abs(item[1])- centre_value)[2][0]# 
    # def select_keys_by_value(d):
    #     mid_range = {k: v for k, v in d.items() if 0.2 <= v <= 0.8}
    #     low_range = {k: v for k, v in d.items() if v < 0.2}
    #     high_range = {k: v for k, v in d.items() if v > 0.8}

    #     if mid_range:
    #         # Return all keys with values in median range
    #         return list(mid_range.keys())
    #     elif low_range:
    #         # Return all keys with the max value under 0.2
    #         max_low = max(low_range.values())
    #         return [k for k, v in low_range.items() if v == max_low]
    #     elif high_range:
    #         # Return all keys with the min value above 0.8
    #         min_high = min(high_range.values())
    #         return [k for k, v in high_range.items() if v == min_high]
    #     else:
    #         return []


    print('Selected Question')
    print('-'*50)
    print(f"{q[closest_key]:.2f}:{closest_key}")

    question=closest_key
    print(time.perf_counter()-start_time)
    # convert(question)
    print(time.perf_counter()-start_time)


    QA[question]=qa[question]
    return question

@app.route('/run-function', methods=['GET'])
def run_function():

    param1 = request.args.get('param1', default="")                                                        #das
    param2 = request.args.get('param2', default="i would like to become an accountant")                    #das

    # param_value = request.args.get('param', default="i would like to become an accountant")
    
    print("This is resume : ",param1,"\n\n\n\n","This is answer : ",param2,end="\n")                       #das
    result = aspira(param2)  

    return jsonify({'result': result})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({"username": username, "password": hashed_pw})

    return jsonify({"message": "User created successfully"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if bcrypt.check_password_hash(user["password"], password):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


if __name__ == '__main__':
    app.run(debug=False, port=5000)
    # app.run(host='0.0.0.0')

# aspira()

