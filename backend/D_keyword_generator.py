
import time
import fitz  # PyMuPDF
from keybert import KeyBERT
import yake
import spacy
nlp = spacy.load("en_core_web_sm")

import logging

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('log/D_keyword_generator.log')
if not logger.hasHandlers():
    logger.addHandler(file_handler)

logger.debug("This is a test log message")


kw_model = KeyBERT()


with open("file/jobs.txt", "r") as file:
    job_list = {line.strip().lower() for line in file if line.strip()}  # Store jobs in a set


def is_job(text):


    text_lower = text.lower()
    word = 'chief ' + text_lower
    return any( job ==text_lower or job ==word for job in job_list)  


from keybert import KeyBERT

def keyword_extraction(text):
    start_time=time.perf_counter()



    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1,2))
    result = [(x, y / 10) for (x, y) in kw_model.extract_keywords(text, keyphrase_ngram_range=(2,3))]
    keywords.extend(result)

    logger.info(f"KeyGen-Time taken: %.4f seconds{ time.perf_counter() - start_time}")
    return dict(keywords)



def extract_verbs_and_entities(text):
    
    doc = nlp(text)
    
    unimportant_words = []
    for token in doc:
        if token.pos_ == "VERB":
            lemma = token.lemma_.lower()
            if lemma not in unimportant_words:
                unimportant_words.append(lemma)
    
    # entities = [(ent.text, ent.label_) for ent in doc.ents]
    unimportant_words.extend([ent.text for ent in doc.ents])
    return unimportant_words


def extract(text):
    unique_keywords = {}
    start_time = time.time()

    logger.debug("\n=== YAKE + Verb/Entity Filtering ===")
    unimportant_words = extract_verbs_and_entities(text)
    logger.debug(f"Verbs & Entities to skip: {unimportant_words}")

    kw_extractor = yake.KeywordExtractor(lan="en", n=2)
    kw_extractor2=yake.KeywordExtractor(lan="en", n=3)
    keywords = kw_extractor.extract_keywords(text)
    keywords.extend(kw_extractor2.extract_keywords(text))
    
    for kw, score in keywords:
        if  not any(kw.find(word)!=-1 for word in  []):
            unique_keywords[kw] =unique_keywords.get(kw,0)*2 + score


    logger.info(f"keyword Gen-Time taken:{time.time() - start_time}")
    return unique_keywords

# Function to extract entities and verbs



if __name__=="__main__":
    text = '''Machine learning teaches computers to recognize patterns and make decisions automatically using data and algorithms.
It can be broadly categorized into three types: supervised learning , unsupervised learning and reinforcment learning'''
    # text ='i like to have accountant job'
    logger.info(''.join(f"\n{k}:\t{v}" for k, v in keyword_extraction(text).items()))
    print(extract_verbs_and_entities(text))
    logger.info(''.join(f"\n{k}:\t{v}" for k, v in extract(text).items()))

    