from recorder import speech
from keyword_generator import extract
from Search_Engine import search  
from Parser import Parse
from chatbot import chatbot
from Summaraizer import split_text_into_chunks,summrize
from speaker import convert
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
# Initialize the model
import time
from flask import Flask, jsonify
import random

app = Flask(__name__)

start_time=time.perf_counter()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to compute similarity between two sentences
def compute_similarity(sentence1, sentence2):
    # Convert sentences to embeddings
    embeddings1 = model.encode([sentence1])
    embeddings2 = model.encode([sentence2])

    # Compute cosine similarity between the embeddings
    similarity_score = cosine_similarity(embeddings1, embeddings2)[0][0]

    return similarity_score


qa={}
timer=4
question ="what is machine learning"
#or question= "what subjects do you like?"
#convert(question)
kw={}

def aspira():
    #while(timer!=0):
        time-=1
        text = '''Machine learning teaches computers to recognize patterns and make decisions automatically using data and algorithms.

    It can be broadly categorized into three types:

    Supervised Learning: Trains models on labeled data to predict or classify new, unseen data.
    Unsupervised Learning: Finds patterns or groups in unlabeled data, like clustering or dimensionality reduction.
    Reinforcement Learning: Learns through trial and error to maximize rewards, ideal for decision-making tasks.
    In addition these categories, there are also Semi-Supervised Learning and Self-Supervised Learning. 

    Semi-Supervised Learning uses a mix of labeled and unlabeled data, making it helpful when labeling data is costly or time-consuming. 
    Self-Supervised Learning creates its own labels from raw data, allowing it to learn patterns without needing labeled examples. 
    Machine Learning Pipeline
    Machine learning is fundamentally built upon data, which serves as the foundation for training and testing models. Data consists of inputs (features) and outputs (labels). A model learns patterns during training and is tested on unseen data to evaluate its performance and generalization. In order to make predictions, there are essential steps through which data passes in order to produce a machine learning model that can make predictions.'''
        text='i very much like machine learning'
        #text='Not found'
        while(text == "Not found"):
            text=speech() 
            if text =="stop":
                break       
        keywords=extract(text)
        #if len(list(keywords.values)) < 2 and all(x < 8 for x in list(keywords.values)):
        #   convert('ok')
        
        for  key , score in keywords.items():
            sm=compute_similarity('machine learning',key)
            kw[key] = (score,sm)
            #value = my_dict.pop('b')

            # print(f"{sm:.2f}:{score:.2f}:{key}")
        #kw={name:kw.get(name,0)+keywords[name] for name in set(kw)| set(keywords)}
        # sorted_scores = dict(sorted(kw.items(), key=lambda x: x[1], reverse=True))
        # sorted_scores= dict(sorted(kw.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True))

        # Calculate the thresholds
        first_elements = [v[0] for v in kw.values()]
        second_elements = [v[1] for v in kw.values()]

        first_threshold = sorted(first_elements)[len(first_elements) // 2]  # Middle of first elements
        second_threshold = sorted(second_elements)[len(second_elements) // 2]  # Middle of second elements

        # Print the thresholds for clarity
        print(f"First threshold: {first_threshold}")
        print(f"Second threshold: {second_threshold}")

        # Sorting based on custom conditions:
        sorted_scores = dict(sorted(kw.items(), key=lambda x: (
            # Check if both values are high (greater than their respective thresholds)
        not (x[1][0] <= first_threshold and x[1][1] <= second_threshold), 
            x[1][1],  # Then sort by the first element
            x[1][0]  # Then sort by the second element
        ), reverse=True))


        for  key , score in sorted_scores.items():
            f_score = (f"{score[0]:.2f}", f"{score[1]:.2f}")

            print(f"{f_score}:{key}")
        kw=sorted_scores
        count1=3
        for  key , score in keywords.items() :
            if score >= 2 and len(key.split(' ')) < 4   :
                count1 -=1
                if (count1==0):
                    break
                links =search(key,no=2)
                for  no , link in enumerate(links,1):
                    text =Parse(link)
                    if text == 'skip' or text is None:
                        continue
                    # with open(f'file/{no}.txt','w') as file:
                    #     file.writelines(text)

                    chunks = split_text_into_chunks(text, max_tokens=200)
                    
                    final_summary = "{}{}{}".join(chunks)
                    # with open('file/summary.txt','w') as file:
                    #     file.writelines(final_summary)
                    print(len(chunks))
                    count=0
                        
                    for i in range(min(len(chunks),5)):
                        l=chatbot(chunks[i])
                        while(count!=3):
                            #convert(l)
                            count+=1
                        score = compute_similarity(question, l)
                        qa[l]=score


        sorted_qa = dict(sorted(qa.items(), key=lambda x: x[1], reverse=True))
        values = list(sorted_qa.values())
        # mean_value = sum(values) / len(values)
        centre_value=np.mean(values)
        closest_key = min(sorted_qa, key=lambda k: abs(sorted_qa[k] - centre_value))
        print('Selected Question')
        print('-'*50)
        print(f"{sorted_qa[closest_key]:.2f}:{closest_key}")
        question=closest_key
        print(time.perf_counter()-start_time)

        convert(question)
        print(time.perf_counter()-start_time)

        yield jsonify({'result':'stop'})





                





            
