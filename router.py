import ollama

def classify_intent(prompt):

    prompt_lower = prompt.lower()

    action_keywords = [
        "chụp màn hình", "screen", "mấy giờ", "thời gian", "âm lượng", "mở nhạc", "tắt máy", "mở ứng dụng", "youtube"
    ]

    for word in action_keywords:
        if word in prompt_lower:
            print(f"tìm thấy từ khóa '{word}' -> ACTION")
            return "ACTION"

    system_prompt = """
    Phân loại:
    1. WEB: hỏi thời tiết, kiến thức thực tế,...
    2. MEMORY:
    - Người dùng hỏi về bản thân họ: "tôi tên là gì", "tôi là ai", "nhà tôi ở đâu", "bạn nhớ gì về tôi"
    - Người dùng nhắc lại chuyện cũ: "hôm qua tôi nói gì", "chúng ta đã bàn về cái gì"
    - Người dùng yêu cầu ghi nhớ: "hãy nhớ tên tôi là...", "lưu lại nhé"
    3. CHAT: trò chuyện xã giao, tình cảm, viết code

    OUTPUT JSON: {"type": "WEB" | "MEMORY" | "CHAT"}
    """
    
    try:
        response = ollama.chat(
            model='llama3',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
        )

        decision = response['message']['content'].strip().upper()
        
        decision = decision.replace(".", "").replace('"', "").strip()
        
        print(f"🧭 Router quyết định: {decision}")

        if "WEB" in decision: 
            return "WEB"
        elif "MEMORY" in decision: 
            return "MEMORY"
        else: 
            return "CHAT"

    except Exception as e:
        print(f"❌ Lỗi Router: {e}")
        return "CHAT"