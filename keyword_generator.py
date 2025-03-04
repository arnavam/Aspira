import nltk
from rake_nltk import Rake
from transformers import pipeline
import time
import fitz  # PyMuPDF
from keybert import KeyBERT

nltk.download('stopwords',download_dir='file')
nltk.download('punkt',download_dir='file')
# nltk.download('punkt_tab',download_dir='~/Developer/Ai_interviewer')
nltk.download('punkt_tab')
r = Rake() 
a={}

with open("file/jobs.txt", "r") as file:
    job_list = {line.strip().lower() for line in file if line.strip()}  # Store jobs in a set

def is_job(text):

    text_lower = text.lower()
    return any(job in text_lower for job in job_list)

# from textblob import TextBlob

# def get_sentiment_score(text):
#     # Create a TextBlob object
#     blob = TextBlob(text)
    
#     # Get the sentiment polarity score (ranges from -1 to 1)
#     sentiment_score = blob.sentiment.polarity




# Proceed with extracting keywords from the uploaded PDF

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
    start_time=time.time()
    r.extract_keywords_from_text(text)    # Extract keywords from the text
    keywords = r.get_ranked_phrases_with_scores()    # Get the ranked keywords
    print('\n')
    print('Keywords')
    for score, kw in keywords:
            if is_job(kw) :
                  continue
            a[kw] =a.get(kw,0) + score


    #print("\n".join(f'{score:.2f}: {kw}' for kw, score in a.items()))

#     classifier = pipeline("zero-shot-classification")
#     output=classifier(
#     "machine learning",
#     candidate_labels=list(a.keys()),
# )
    # print(output)
    sorted_scores = dict(sorted(a.items(), key=lambda x: x[1], reverse=True))# Sort by value in descending order

    print(time.time()-start_time)
    return sorted_scores