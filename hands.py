import webbrowser
import datetime
import os
import platform
import ollama
import json

def open_website(url):
	webbrowser.open(url)
	return f"Đã mở trang web: {url}"

def play_music_on_youtube(song_name):
	url = f"https://www.youtube.com/results?search_query={song_name.replace(' ', '+')}"
	webbrowser.open(url)
	return f"Đang tìm và mở bài '{song_name}' trên Youtube"

def get_current_time():
	now = datetime.datetime.now().strftime("%H:%M ngày %d/%m/%Y")
	return f"Bây giờ là: {now}"

def open_app(app_name):
	try:
		if "calc" in app_name.lower():
			os.system("start calc")
			return "Đã mở máy tính mini"
		elif "note" in app_name.lower():
			os.system("start notepad")
			return "Đã mở Notepad"
		else:
			return f"Xin lỗi nhé, tôi chưa biết cách mở ứng dụng {app_name}"
	except Exception as e:
		return f"Lỗi khi mở ứng dụng: {e}"

def execute_action(user_prompt):
	system_prompt = """
    Bạn là một trình điều khiển máy tính. Nhiệm vụ: Phân tích yêu cầu người dùng và trích xuất hành động dưới dạng JSON.
    
    Các công cụ khả dụng:
    1. OPEN_WEB: Dùng khi người dùng muốn mở trang web (google, facebook, vnexpress...).
       - Tham số: "url" (link đầy đủ).
    2. YOUTUBE: Dùng khi người dùng muốn nghe nhạc, xem video.
       - Tham số: "song" (tên bài hát/video).
    3. TIME: Dùng khi hỏi giờ.
       - Tham số: Không cần.
    4. APP: Dùng khi mở ứng dụng (calculator, notepad).
       - Tham số: "app_name".
    
    OUTPUT FORMAT (JSON ONLY):
    Ví dụ 1: "Mở nhạc Sơn Tùng" -> {"tool": "YOUTUBE", "val": "Sơn Tùng"}
    Ví dụ 2: "Mở facebook" -> {"tool": "OPEN_WEB", "val": "https://facebook.com"}
    Ví dụ 3: "Mấy giờ rồi" -> {"tool": "TIME", "val": ""}
    
    CHỈ TRẢ VỀ JSON, KHÔNG GIẢI THÍCH.
    """

	try:
   		response = ollama.chat(
   			model = 'llama3',
   			messages = [
   				{'role': 'system', 'content': system_prompt},
   				{'role': 'user', 'content': user_prompt}
   			]
   		)

   		content = response['message']['content'].strip()
   		start = content.find('{')
   		end = content.rfind('}') + 1
   		
   		if start != -1 and end != -1:
   			json_str = content[start:end]
   			action_data = json.loads(json_str)

   			tool = action_data.get("tool")
   			val = action_data.get("val")

   			if tool == "OPEN_WEB":
   				return open_website(val)
   			elif tool == "YOUTUBE":
   				return play_music_on_youtube(val)
   			elif tool == "TIME":
   				return get_current_time()
   			elif tool == "APP":
   				return open_app(val)
   			else:
   				return "tôi không hiểu lệnh hành động này, hãy thiết lập thêm"
   		else:
   			return "Lỗi: không thể xác định đúng định dạng JSON"

	except Exception as e:
   		print(f"Lỗi Action: {e}")
   		return "Có lỗi khi thực hiện hành động"