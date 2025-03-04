from transformers import pipeline
import math

def split_text_into_chunks(text, max_tokens=1024):
        # Approximate word tokenization: 1 token ≈ 3/4 of a word
        words = text.split()
        max_words_per_chunk = max_tokens * 3 // 4
        chunks = [words[i:i+max_words_per_chunk] for i in range(0, len(words), max_words_per_chunk)]
        return [" ".join(chunk) for chunk in chunks]

def summrize(text,max_tokens=200):
    # Initialize summarizer
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    # Function to split text into chunks
    

    # # Sample long text
    # long_text = """
    # Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving." ...
    # """  # Make sure this text is long enough to exceed the token limit

    # Split the text into smaller chunks
    chunks = split_text_into_chunks(text, max_tokens)
    
    # Summarize each chunk
    summaries = [summarizer(chunk, max_length=len(chunk.split())//2, min_length=len(chunk.split())//4, do_sample=False)[0]['summary_text'] for chunk in chunks]

    # Combine the individual summaries into one
    print('f')
    
    return summaries