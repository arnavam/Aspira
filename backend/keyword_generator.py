import nltk
from rake_nltk import Rake
from transformers import pipeline
import time
import fitz  # PyMuPDF
from keybert import KeyBERT

import spacy
from spacy.cli import download

# Load the pre-trained spaCy model
# nlp = spacy.load("en_core_web_trf")
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

nltk.download('stopwords',download_dir='file')
nltk.download('punkt',download_dir='file')
# nltk.download('punkt_tab',download_dir='~/Developer/Ai_interviewer')
nltk.download('punkt_tab')




r = Rake() 

with open("file/jobs.txt", "r") as file:
    job_list = {line.strip().lower() for line in file if line.strip()}  # Store jobs in a set


def is_job(text):


    text_lower = text.lower()
    word = 'chief ' + text_lower
    return any( job ==text_lower or job ==word for job in job_list)  


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")

    return text

def extract_keywords_from_pdf(pdf_path, num_keywords=10):

    resume_text = extract_text_from_pdf(pdf_path)
    kw_model = KeyBERT()
    keywords_with_scores = kw_model.extract_keywords(resume_text, keyphrase_ngram_range=(1, 2), top_n=num_keywords)

    return keywords_with_scores


def extract(text):
    unique_keywords={}
    start_time=time.time()
    r.extract_keywords_from_text(text)    
    keywords = r.get_ranked_phrases_with_scores()    # Get the ranked keywords
    print('\n')
    print('Keywords')
    word_list=extract_verbs_and_entities(text)
    print(word_list)

    for score, kw in keywords:
                
        if  not any(kw.find(word)!=-1 for word in  word_list):
            unique_keywords[kw] =unique_keywords.get(kw,0)*2 + score





#     classifier = pipeline("zero-shot-classification")
#     output=classifier(
#     "machine learning",
#     candidate_labels=list(a.keys()),
# )
    # print(output)

    print(time.time()-start_time)
    return unique_keywords



# Function to extract entities and verbs

def extract_verbs_and_entities(text):
    
    doc = nlp(text)
    
    important_words = []
    for token in doc:
        if token.pos_ == "VERB":
            lemma = token.lemma_.lower()
            if lemma not in important_words:
                important_words.append(lemma)
    
    # entities = [(ent.text, ent.label_) for ent in doc.ents]
    important_words.extend([ent.text for ent in doc.ents])
    return important_words



if __name__=="__main__":
    text = '''Machine learning teaches computers to recognize patterns and make decisions automatically using data and algorithms.
        It can be broadly categorized into three types:
        supervised learning , unsupervised learning and reinforcment learning'''
    text ='i like to have accountant job'
    print(extract(text))