# import nltk
# nltk.download('punkt_tab')

def correcting2 (text):
    from textblob import TextBlob
    words=[]
    for word in text.split():
        corrected = TextBlob(word).correct()
        # print(f"Original: {word} →  {corrected}")
        words.append(corrected.string)
    print(words)
    return " ".join(words)

    
def scoring(text):
    from textblob import TextBlob
    blob = TextBlob(text)
    sentiment=blob.sentiment
    print("Sentiment Analysis:",sentiment ) # Sentiment (-1 to +1)
    print("Noun Phrases:", blob.noun_phrases)
    polarity = sentiment.polarity
    subjectivity=blob.sentiment.subjectivity

    print("Polarity:", polarity) 
    print("Subjectivity:",subjectivity ) 
    return subjectivity, polarity, list(blob.noun_phrases)


def scoring2(text):
    import textstat

    # flesch_kincaid_score = textstat.flesch_kincaid_grade(text)
    explainablity = textstat.flesch_reading_ease(text)
    technicality = textstat.gunning_fog(text)
    depth =textstat.smog_index(text)

    print("ARI:", textstat.automated_readability_index(text))
    print("Dale-Chall:", textstat.dale_chall_readability_score(text))
    print("Syllable Count:", textstat.syllable_count(text))
    print("Difficult Words:", textstat.difficult_words(text))



    return explainablity, technicality , depth

if __name__=="__main__":
    text = """
machine learning is a stdy of how does input variable map to output varaible and how to can we learn it find the correct relation ,it  is mainly divided into supervised unsupervised and reinforcment learning
"""
    text=correcting2(text)
    print(text)
    scoring(text)
    scoring2(text)
