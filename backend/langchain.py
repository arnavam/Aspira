# from langchain import LLMChain
# from langchain.llms import HuggingFaceHub, HuggingFacePipeline
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain.document_loaders import WebBaseLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import FAISS
# from langchain.chains import ConversationalRetrievalChain
# from langchain.memory import ConversationBufferMemory
# from langchain.prompts import PromptTemplate

# # 1. Setup LLM
# llm = HuggingFaceHub(
#     repo_id="your‐hf‐instruct‐model",  # e.g. “google/flan-t5-large” or something that supports instruction
#     model_kwargs={"temperature":0.7, "max_length":512}
# )

# # 2. Setup embeddings
# embeddings = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/paraphrase-multilingual-MiniLM‑L12‑v2"
# )

# # 3. Document loader + web retrieval
# # Given some URLs or topics, load content
# loader = WebBaseLoader(web_paths=[ "https://example.com/article1", "https://example.com/article2" ])
# docs = loader.load()

# # 4. Split documents
# splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# doc_chunks = splitter.split_documents(docs)

# # 5. Build vector store
# vector_store = FAISS.from_documents(doc_chunks, embeddings)

# # 6. Retriever
# retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# # 7. Memory for conversation history
# memory = ConversationBufferMemory()

# # 8. Prompt template
# prompt = PromptTemplate(
#     input_variables=["history", "question", "context"],
#     template="""
# You are an AI interviewer. Use the following retrieved context to generate the next question in the interview.

# Context:
# {context}

# Conversation history:
# {history}

# Latest question asked:
# {question}

# Now ask the next relevant question to the candidate, taking into account the candidate’s answer and the retrieved context.
# """
# )

# # 9. Chain
# interview_chain = ConversationalRetrievalChain.from_llm(
#     llm=llm,
#     retriever=retriever,
#     memory=memory,
#     combine_docs_chain_kwargs={"prompt": prompt}
# )

# # 10. Run the interview loop
# def run_interview():
#     print("AI Interviewer: Hello, let's start with your background. What has been your recent work experience?")
#     while True:
#         candidate_input = input("You: ")
#         if candidate_input.lower() in ["exit","quit","stop"]:
#             print("AI Interviewer: Thank you for your time. Goodbye!")
#             break
#         resp = interview_chain({"question": candidate_input})
#         # The response will contain “answer” (the next question)
#         print("AI Interviewer:", resp["answer"])
