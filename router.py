import ollama

def classify_intent(prompt):
	system_prompt = """
	Bạn là một AI Router thông minh. Nhiệm vụ của bạn là phân loại câu hỏi của người dùng vào 1 trong 3 nhóm sau:
    
    1. ACTION: Nếu người dùng yêu cầu thực hiện hành động trên máy tính (mở nhạc, mở web, mở app, xem giờ, tắt máy...).
    2. WEB: Nếu hỏi thông tin thực tế cần tra cứu (thời tiết, giá vàng, tin tức...).
    3. MEMORY: Nếu hỏi về bản thân AI hoặc tài liệu đã học.
    4. CHAT: Các cuộc trò chuyện xã giao, giải thích, code, dịch thuật.
    
    CHỈ TRẢ VỀ 1 TỪ: "ACTION", "WEB", "MEMORY", HOẶC "CHAT".
    """
	try:
		response = ollama.chat(
			model = 'llama3',
			messages = [
				{'role': 'system', 'content': system_prompt},
				{'role': 'user', 'content': prompt}
			]
		)

		decision = response['message']['content'].strip().upper()
		print(f"Router đã chọn: {decision}")

		if "ACTION" in decision: return "ACTION"
		if "WEB" in decision: return "WEB"
		if "MEMORY" in decision: return "MEMORY"
		return "CHAT"

	except Exception as e:
		print(f"Lỗi Router: {e}")
		return "CHAT"