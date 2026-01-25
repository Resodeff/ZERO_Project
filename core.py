from langchain_community.llms import Ollama

def load_brain():
	print("...đang khởi động ZERO...")
	model = Ollama(model="llama3", temperature=0.7)
	return model