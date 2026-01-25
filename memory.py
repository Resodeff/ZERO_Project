import sys
try:
	__import__('pyslite3')
	sys.modules['slite3'] = sys.modules.pop('pyslite3')
except ImportError:
	pass

import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_PATH= "./data/memory_db"

def load_memory():
	embeddings_model = OllamaEmbeddings(model="nomic-embed-text")

	vector_db = Chroma(
		persist_directory = DB_PATH,
		embedding_function = embeddings_model,
		collection_name = "Aley_memories"
	)

	return vector_db

def save_to_memory(vector_db, file_path):
	if file_path.endswith(".pdf"):
		loader = PyPDFLoader(file_path)
	else:
		loader = TextLoader(file_path, encoding="utf-8")

	documents = loader.load()

	text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
	chunks = text_splitter.split_documents(documents)

	vector_db.add_documents(chunks)
	return len(chunks)

def save_history_to_memory(vector_db, text):
	vector_db.add_texts(texts=[text])

def search_memory(vector_db, query, k=3):
	results = vector_db.similarity_search(query, k = k)
	return [doc.page_content for doc in results]
