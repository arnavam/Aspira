import language_tool_python
from textblob import TextBlob
import textstat

tool = language_tool_python.LanguageTool('en-US')


def correcting(text):
    matches = tool.check(text)

    corrected_paragraph = language_tool_python.utils.correct(text, matches)
    # for match in matches:
    #     print(f"Error: {match.message}")
    #     print(f"Context: {match.context}")
    #     print(f"Suggested correction: {match.replacements}\n")

    return corrected_paragraph

def scoring(text):

    blob = TextBlob(text)
    sentiment=blob.sentiment
    print("Sentiment Analysis:",sentiment ) # Sentiment (-1 to +1)
    print("Noun Phrases:", blob.noun_phrases)
    polarity = sentiment.polarity
    subjectivity=blob.sentiment.subjectivity

    print("Polarity:", polarity) 
    print("Subjectivity:",subjectivity ) 
    return subjectivity, polarity


def scoring2(text):
    # flesch_kincaid_score = textstat.flesch_kincaid_grade(text)
    explainablity = textstat.flesch_reading_ease(text)
    technicality = textstat.gunning_fog(text)
    depth =textstat.smog_index(text)

    # print("ARI:", textstat.automated_readability_index(text))
    # print("Dale-Chall:", textstat.dale_chall_readability_score(text))
    # print("Syllable Count:", textstat.syllable_count(text))
    # print("Difficult Words:", textstat.difficult_words(text))



    return explainablity, technicality , depth

if __name__=="__main__":
    text = """
machine learning is a study of how does input variable map to output varaible and how to can we learn it find the correct relation ,it  is mainly divided into supervised unsupervised and reinforcment learning
"""
