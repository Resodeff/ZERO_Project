from langchain_community.llms import Ollama

def load_brain(model_name="llama3"):
	print(f"...đang khởi động ZERO...")
	print(f"áp dụng model: {model_name}")
	model = Ollama(model=model_name, temperature=0.7)
	return model