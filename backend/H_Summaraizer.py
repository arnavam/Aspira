from transformers import pipeline
from textblob import TextBlob


def split_text_into_chunks(text, max_tokens=1024):
        # Approximate word tokenization: 1 token ≈ 3/4 of a word
        words = text.split()
        max_words_per_chunk = max_tokens * 3 // 4
        chunks = [words[i:i+max_words_per_chunk] for i in range(0, len(words), max_words_per_chunk)]
        return [" ".join(chunk) for chunk in chunks]


def split_text_into_sentence_chunks(text, max_tokens=1024):

    blob = TextBlob(text)
    sentences = [str(sentence).strip() for sentence in blob.sentences]

    chunks = []
    current_chunk = []
    current_length = 0
    max_words_per_chunk = max_tokens * 3 // 4  # approximate word limit

    for sentence in sentences:
        sentence_length = len(sentence.split())
        # If adding this sentence exceeds chunk limit, start a new chunk
        if current_length + sentence_length > max_words_per_chunk and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    # Add the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks




def summrize(text,max_tokens=200):

    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    # long_text = """
    # Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving." ...
    # """  # Make sure this text is long enough to exceed the token limit
    chunks = split_text_into_chunks(text, max_tokens)
    summaries = [summarizer(chunk, max_length=len(chunk.split())//2, min_length=len(chunk.split())//4, do_sample=False)[0]['summary_text'] for chunk in chunks]
    print('f')
    
    return summaries

if __name__=='__main__':
        large_text = """
        Wikipedia is a free online encyclopedia, created and edited by volunteers around the world and hosted by the Wikimedia Foundation.
        The 30 million articles in English have about 5 million editors, and more than 500 million articles exist in all languages.
        Content is written collaboratively by largely anonymous volunteers who write without pay.
        Anyone with internet access can write and make changes to Wikipedia articles, except in limited cases where editing is restricted to prevent disruption or vandalism.
        """

        chunks = split_text_into_sentence_chunks(large_text, max_tokens=50)
        print(f"Total chunks: {len(chunks)}{type(chunks)}")
        for i, chunk in enumerate(chunks, 1):
                print(f"\nChunk {i}:\n{chunk}")