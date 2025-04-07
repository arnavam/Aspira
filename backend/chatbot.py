import torch

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import time
from sentence_transformers import SentenceTransformer
import numpy as np

from huggingface_hub import login
with open('tokens/hugging.txt', 'r') as file:

    hf_token = file.read().strip()

login(token=hf_token)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained("p208p2002/bart-squad-qg-hl")
model_chat = AutoModelForSeq2SeqLM.from_pretrained("p208p2002/bart-squad-qg-hl")
# tokenizer = AutoTokenizer.from_pretrained("p208p2002/t5-squad-qg-hl")
# model = AutoModelForSeq2SeqLM.from_pretrained("p208p2002/t5-squad-qg-hl")
# model=torch.jit.script(model).to_device(device)
model_chat.eval()


import torch
import time

def chatbot(input_text_batch):
    # Start measuring time
    start_time = time.time()

    # Batch encode the input texts (a list of strings)
    input_ids = tokenizer.batch_encode_plus(
        input_text_batch, 
        return_tensors="pt", 
        padding=True,   # Pads sequences to the longest length in the batch
        truncation=True, # Optionally truncate if sequences are too long
        max_length=100  # Optional: specify max length
    ).to(device)

    # Generate output for each input in the batch
    with torch.no_grad():
        output_ids = model_chat.generate(
            input_ids['input_ids'],  # Use the 'input_ids' from batch_encode_plus
            max_length=100, 
            num_return_sequences=1, 
            no_repeat_ngram_size=2, 
            top_p=0.95, 
            top_k=60, 
            temperature=0.8,
            do_sample=True
        )

    # Decode the output texts
    generated_texts = [tokenizer.decode(output, skip_special_tokens=True) for output in output_ids]

    # Print the generated responses
    for text in generated_texts:
        print(text)
    
    # Print time taken for the batch processing
    print(f"Time taken for batch processing: {time.time() - start_time:.4f} seconds")
    
    return generated_texts


from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model_sim = SentenceTransformer('all-MiniLM-L6-v2',device=device)

def similarity_score(sentence1, sentence2):
    embeddings1 = model_sim.encode([sentence1])
    embeddings2 = model_sim.encode([sentence2])

    similarity_score = cosine_similarity(embeddings1, embeddings2)[0][0]

    return similarity_score.item()



# Load model once (outside the function)

def similarity_score2(target_sentence, other_sentences):

    # Encode target once
    target_embedding = model_sim.encode([target_sentence], convert_to_tensor=True)
    
    # Batch encode all other sentences
    other_embeddings = model_sim.encode(other_sentences, convert_to_tensor=True, batch_size=128)
    
    # Compute cosine similarity using matrix multiplication
    similarities = np.dot(target_embedding.cpu().numpy(), 
                         other_embeddings.cpu().numpy().T).flatten()
    
    return {sentence: float(score) 
            for sentence, score in zip(other_sentences, similarities)}
# from sentence_transformers import SentenceTransformer
# from sklearn.cluster import DBSCAN
# from sklearn.metrics.pairwise import cosine_similarity
# import numpy as np

# # Step 1: Convert sentences to embeddings
# sentences = [
#     "Data science is an inter-disciplinary field.",
#     "Machine learning is a subfield of artificial intelligence.",
#     "Artificial intelligence is transforming various industries.",
#     "Data analysts use various techniques to analyze data.",
#     "Deep learning models are a subset of machine learning.",
#     "The economy is improving due to various reforms.",
#     "Environmental science is a crucial field for sustainable development.",
#     "Quantum computing will change the future of technology."
# ]

# # Initialize Sentence-BERT model
# model = SentenceTransformer('all-MiniLM-L6-v2')

# # Encode the sentences into embeddings
# embeddings = model.encode(sentences)

# # Step 2: Use DBSCAN to cluster sentences without specifying the number of clusters
# db = DBSCAN(eps=0.5, min_samples=2, metric='cosine')  # You can adjust eps and min_samples
# db.fit(embeddings)

# # Step 3: Identify the cluster of a given sentence
# target_sentence = "I want to learn about machine learning."

# # Convert the target sentence into its embedding
# target_embedding = model.encode([target_sentence])

# # Step 4: Find the cluster label of the target sentence
# target_label = db.labels_[np.argmin(cosine_similarity(target_embedding, embeddings))]

# # Step 5: Find sentences in the same cluster
# cluster_sentences = [sentences[i] for i in range(len(sentences)) if db.labels_[i] == target_label]

# # Print the result
# print(f"The group most similar to the sentence '{target_sentence}' is:")
# print(cluster_sentences)


#----

# outputs = model.generate(
#     **inputs, 
#     max_length=50, 
#     output_scores=True, 
#     return_dict_in_generate=True
# )

# # Get scores (list of tensors of shape [batch_size, vocab_size])
# scores = outputs.scores
# sequences = outputs.sequences

# batch_size = sequences.shape[0]
# seq_length = sequences.shape[1]

# log_probs = []
# for idx in range(batch_size):
#     total_log_prob = 0.0
#     for step in range(seq_length - 1):  # Skip prompt
#         token_id = sequences[idx, step + 1]  # Next token
#         logits = scores[step][idx]  # Logits for this step
#         log_prob = logits.log_softmax(dim=0)[token_id].item()
#         total_log_prob += log_prob
#     log_probs.append(total_log_prob)

# Lower total_log_prob = Higher complexity

# outputs = model.generate(
#     **inputs, 
#     max_length=50, 
#     num_beams=2, 
#     return_dict_in_generate=True
# )

# # Shape: [batch_size * num_return_sequences]
# beam_scores = outputs.sequences_scores  


# for text in texts:
#     # Track memory usage before the inference
#     memory_before = psutil.virtual_memory().used

#     # Measure time for the question
#     start_time = time.time()
#     result = model(text)
#     end_time = time.time()

#     # Track memory usage after the inference
#     memory_after = psutil.virtual_memory().used

#     # Calculate the time taken for this question
#     time_taken = end_time - start_time

#     # Calculate the memory used during this question's processing
#     memory_used = memory_after - memory_before

#     # Store the results
#     times_per_question.append(time_taken)
#     memory_usage_per_question.append(memory_used)