import webbrowser
from datetime import datetime, timedelta, timezone
import os
import platform
import ollama
import json
import pyautogui
import time 

ACTIONS = {
    ("chụp màn hình", "screenshot", "screen shot"): lambda: take_screenshot(0),
    ("giờ", "thời gian"): lambda: get_current_time(),
    ("tăng âm lượng"): lambda: system_volume("UP"),
    ("giảm âm lượng"): lambda: system_volume("DOWN"),
    ("tắt am thanh", "tắt tiếng"): lambda: system_volume("MUTE"),
    ("tắt máy", "shutdown"): lambda: system_power("SHUTDOWN"),
    ("khởi động lại", "restart"): lambda: system_power("RESTART"),
    ("hủy", "dừng lại"): lambda: system_power("ABORT"),
}

def open_website(url):
    webbrowser.open(url)
    return f"Đã mở trang web: {url}"

def play_music_on_youtube(song_name):
    url = f"https://www.youtube.com/results?search_query={song_name.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Đang tìm và mở bài '{song_name}' trên Youtube..."

def get_current_time():
    now = datetime.now()
    full_time = now.strftime("%H:%M ngày %d/%m/%Y")
    print(f"Đã lấy giờ hệ thống: {full_time}")
    return f"Bây giờ là: {full_time} [Giờ Việt Nam]"

def open_app(app_name):
    try:
        if "calc" in app_name.lower():
            os.system("start calc")
            return "Đã mở máy tính bỏ túi."
        elif "note" in app_name.lower():
            os.system("start notepad")
            return "Đã mở Notepad."
        else:
            return f"Xin lỗi, tôi chưa biết cách mở ứng dụng {app_name}."
    except Exception as e:
        return f"Lỗi khi mở ứng dụng: {e}"

def system_volume(action):
    if action == "UP":
        pyautogui.press("volumeup", presses=5)
        return "Đã tăng âm lượng."
    elif action == "DOWN":
        pyautogui.press("volumedown", presses=5)
        return "Đã giảm âm lượng."
    elif action == "MUTE":
        pyautogui.press("volumemute")
        return "Đã tắt/bật tiếng."

def take_screenshot(delay = 0):
    try:
        delay_sec = int(delay)
    except:
        delay_sec = 0
    
    if delay_sec > 0:
        print(f"📸 Chuẩn bị chụp sau {delay_sec} giây...")
        time.sleep(delay_sec)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_path = os.path.join(base_dir, "zero_img")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_name = f"screenshot_{int(time.time())}.png"
    full_path = os.path.join(folder_path, file_name)

    try:
        pyautogui.screenshot(full_path)
        print(f"Đã lưu ảnh tại: {full_path}")
        return f"Lưu ảnh tại: {full_path}"

    except Exception as e:
        print(f"Lỗi chụp ảnh: {e}")
        return f"Lỗi khi chụp ảnh: {e}"

def system_power(action):
    if action == "SHUTDOWN":
        os.system("shutdown /s /t 60")
        return "Cảnh báo: Máy sẽ tắt sau 60 giây... Nói 'Hủy' để dừng!"
    elif action == "RESTART":
        os.system("shutdown /r /t 60")
        return "Cảnh báo: Máy sẽ khởi động lại sau 60 giây... Nói 'Hủy' để dừng!"
    elif action == "ABORT":
        os.system("shutdown /a")
        return "Đã hủy lệnh tắt máy."

def execute_action(user_prompt):

    prompt_lower = user_prompt.lower()

    for keywords, func in ACTIONS.items():
        if any(k in prompt_lower for k in keywords):
            try:
                return func()
            except Exception as e:
                return f"Lỗi thực thi {e}"

    print("Lệnh phức tạp -> gọi llama3...")

    system_prompt = """
    Extract command to JSON: {"tool": "YOUTUBE" | "WEB" | "APP", "val": "search term/url/app name"}
    Only JSON.
    """
    
    try:
        response = ollama.chat(
            model='llama3',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )
        
        content = response['message']['content'].strip()
        print(f"Đang suy nghĩ {content}")
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start != -1 and end != -1:
            data = json.loads(content[start:end])
            tool = data.get("tool")
            val = data.get("val")
            
            if tool == "WEB": return open_website(val)
            elif tool == "YOUTUBE": return play_music_on_youtube(val)
            elif tool == "APP": return open_app(val)
            else: return "Chức năng này chưa được cài đặt."
        else:
            return "Lỗi phân tích lệnh của AI."
            
    except Exception as e:
        print(f"Lỗi Action: {e}")
        return "Có lỗi xảy ra khi thực hiện lệnh."