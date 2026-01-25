import ollama

def classify_intent(prompt):
	system_prompt = """
	Bạn là một AI Router thông minh. Nhiệm vụ của bạn là phân loại câu hỏi của người dùng vào 1 trong 3 nhóm sau:
    
    1. WEB: Nếu câu hỏi cần thông tin thực tế, mới nhất (thời tiết, giá vàng, tin tức, ai là, sự kiện năm nay...).
    2. MEMORY: Nếu câu hỏi liên quan đến thông tin cá nhân, tài liệu đã upload, "tôi là ai", "trong file có gì".
    3. CHAT: Các trường hợp còn lại (chào hỏi, viết code, dịch thuật, giải toán, suy luận logic).
    
    CHỈ TRẢ VỀ ĐÚNG 1 TỪ KHÓA: "WEB", "MEMORY" HOẶC "CHAT". KHÔNG GIẢI THÍCH GÌ THÊM.
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

		if "WEB" in decision: return "WEB"
		if "MEMORY" in decision: return "MEMORY"
		return "CHAT"

	except Exception as e:
		print(f"Lỗi Router: {e}")
		return "CHAT"