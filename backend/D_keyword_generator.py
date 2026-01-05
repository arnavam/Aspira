
import time
from logger_config import get_logger

logger = get_logger(__name__)



with open("file/jobs.txt", "r") as file:
    job_list = {line.strip().lower() for line in file if line.strip()}  # Store jobs in a set


def is_job(text):


    text_lower = text.lower()
    word = 'chief ' + text_lower
    return any( job ==text_lower or job ==word for job in job_list)  



def keyword_extraction(text):
    from model_cache import get_keybert
    kw_model = get_keybert()
    start_time=time.perf_counter()



    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1,2))
    result = [(x, y / 10) for (x, y) in kw_model.extract_keywords(text, keyphrase_ngram_range=(2,3))]
    keywords.extend(result)
    
    # Deduplicate: remove longer keywords that contain shorter ones
    keywords = deduplicate_keywords(keywords)

    logger.info(f"KeyGen-Time: {time.perf_counter() - start_time:.2f}s")
    return dict(keywords)


def deduplicate_keywords(keywords: list) -> list:
    """
    Remove longer keywords that contain shorter ones.
    E.g., if 'churn prediction' and 'churn prediction focuses' both exist,
    keep only 'churn prediction'.
    """
    # Sort by length (shorter first)
    sorted_kw = sorted(keywords, key=lambda x: len(x[0]))
    result = []
    
    for kw, score in sorted_kw:
        kw_lower = kw.lower()
        # Check if this keyword is contained in any already-kept keyword
        is_duplicate = False
        for existing_kw, _ in result:
            existing_lower = existing_kw.lower()
            # Skip if current is a substring of existing OR existing is substring of current
            if kw_lower in existing_lower or existing_lower in kw_lower:
                is_duplicate = True
                break
        
        if not is_duplicate:
            result.append((kw, score))
    
    return result



def extract_verbs_and_entities(text):
    from model_cache import get_spacy
    nlp = get_spacy()
    
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

    logger.debug(f"Verbs & Entities to skip: {unimportant_words}")

    import yake
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