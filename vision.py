import ollama

def analyze_image(image_bytes, user_prompt):
	try:
		vision_response = ollama.chat(
			model = 'llava',
			messages = [
				{
				'role' : 'user',
				'content': "Describe this image in detail",
				'images': [image_bytes]
				}
			]
		)
		description = vision_response['message']['content']

		final_response = ollama.chat(
			model = 'Llama3',
			messages = [
				{
					'role': 'system',
					'content': "Bạn là Aley, hãy trả lời câu hỏi của người dùng dựa trên mô tả hình ảnh được cung cấp. Trả lời bằng tiếng Việt tự nhiên, thân thiện."

				},
				{
					'role': 'user',
					'content': f"Mô tả hình ảnh: {description}\n\nCâu hỏi của tôi: {user_prompt}"
				}
			]
		)

		return final_response['message']['content']
	except Exception as e:
		return f"Xin lỗi, Aley bị hoa mắt rồi: {str(e)}"