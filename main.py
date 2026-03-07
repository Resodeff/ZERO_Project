import flet as ft
import asyncio
import speech_recognition as sr
import edge_tts
from langdetect import detect
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

from brain.hands import execute_action
from brain.router import classify_intent
from brain.tools import search_internet
from brain.vision import analyze_image
from brain.core import load_brain
from brain.personality import computer
from brain.memory import load_memory, save_to_memory, search_memory, save_history_to_memory

SECRET_PASSWORD = "123"

# --- HELPER FUNCTIONS ---
def detect_language(text):
    try:
        lang = detect(text)
        return "vi" if lang == "vi" else "en"
    except:
        return "vi"

async def generate_edge_audio(text, lang_code):
    voice = 'vi-VN-NamMinhNeural' if lang_code == 'vi' else 'en-US-ChristopherNeural'
    communicate = edge_tts.Communicate(text, voice)
    temp_filename = "temp_audio_edge.mp3"
    await communicate.save(temp_filename)
    return temp_filename

def speech_to_text_mic():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Đang nghe...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            text = r.recognize_google(audio, language="vi-VN")
            return text
        except Exception:
            return ""

# --- MAIN APP ---
async def main(page: ft.Page):
    page.title = "ZERO - AI Companion"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212" # Màu nền tối sang trọng
    page.padding = 0
    
    # --- GLOBAL STATE ---
    state = {
        "llm": load_brain(),
        "memory_db": load_memory(),
        "pending_image_path": None, # Đường dẫn ảnh đang chờ gửi
        "pending_image_bytes": None
    }

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("human", "Context: {context}\nQuestion: {input}")
    ])
    chain = prompt_template | state["llm"] | StrOutputParser()

    # --- UI COMPONENTS ---

    # 1. Danh sách chat
    chat_list = ft.ListView(
        expand=True,
        spacing=15,
        auto_scroll=True,
        padding=20
    )

    # 2. Audio Player (Ẩn)
    audio_player = ft.Audio(src="start_sound.mp3", autoplay=True)
    page.overlay.append(audio_player)

    # --- CHAT BUBBLE FACTORY ---
    def create_user_bubble(text, image_path=None):
        content_list = []
        if image_path:
            content_list.append(ft.Image(src=image_path, width=200, border_radius=10, fit=ft.ImageFit.CONTAIN))
        content_list.append(ft.Text(text, size=15))

        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(content_list, spacing=5),
                    padding=12,
                    border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15),
                    bgcolor=ft.colors.BLUE_900,
                ),
                ft.CircleAvatar(
                    content=ft.Icon(ft.icons.PERSON),
                    bgcolor=ft.colors.BLUE_GREY_400,
                    radius=16
                )
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    def create_bot_placeholder():
        # Tạo bong bóng chờ với spinner xoay xoay
        status_text = ft.Text("Đang suy nghĩ...", size=12, italic=True, color=ft.colors.GREY_400)
        spinner = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.ORANGE)
        
        content = ft.Container(
            content=ft.Row([spinner, status_text], spacing=10),
            padding=12,
            border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_right=15),
            bgcolor=ft.colors.GREY_900,
        )
        
        row = ft.Row(
            controls=[
                ft.CircleAvatar(content=ft.Image(src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png"), bgcolor=ft.colors.BLACK, radius=16), # Icon Robot
                content
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        return row, status_text, spinner, content

    # --- LOGIC XỬ LÝ CHÍNH ---
    async def process_message(user_input, image_bytes=None, image_path=None):
        if not user_input and not image_bytes: return

        # 1. User Message
        chat_list.controls.append(create_user_bubble(user_input, image_path))
        
        # Reset vùng preview ảnh
        preview_container.visible = False
        state["pending_image_path"] = None
        state["pending_image_bytes"] = None
        await page.update_async()

        # 2. Bot Placeholder (Spinner)
        bot_row, status_txt, spinner, bubble_container = create_bot_placeholder()
        chat_list.controls.append(bot_row)
        await page.update_async()

        final_answer = ""
        
        try:
            # --- VISION MODE ---
            if image_bytes:
                status_txt.value = "👁️ Đang phân tích hình ảnh..."
                await page.update_async()
                
                response = analyze_image(image_bytes, user_input)
                
                # Chuyển từ Spinner sang Text Stream
                spinner.visible = False
                msg_markdown = ft.Markdown("", extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
                bubble_container.content = msg_markdown
                
                for char in response:
                    final_answer += char
                    msg_markdown.value = final_answer + " ▌"
                    await page.update_async()
                    await asyncio.sleep(0.005)
                
                final_answer = response

            # --- TEXT/ROUTER MODE ---
            else:
                intent = classify_intent(user_input)
                context_str = ""
                source_note = ""

                # Cập nhật trạng thái thông minh
                # Cập nhật trạng thái thông minh
                if intent == "ACTION":
                    status_txt.value = "⚙️ Đang thực hiện tác vụ hệ thống..."
                    await page.update_async()
                    
                    # 1. Thực hiện hành động
                    action_result = execute_action(user_input)
                    final_answer = str(action_result)
                    
                    # 2. Hiển thị kết quả ra màn hình
                    spinner.visible = False
                    bubble_container.content = ft.Markdown(final_answer)
                    await page.update_async()

                    # 3. [MỚI] Phát âm thanh ngay tại đây luôn!
                    try:
                        # Actions thường trả về tiếng Việt nên fix cứng "vi" luôn cho nhanh
                        audio_src = await generate_edge_audio(final_answer, "vi") 
                        audio_player.src = audio_src
                        audio_player.update()
                        audio_player.play()
                    except Exception as e:
                        print(f"Lỗi audio action: {e}")

                    # 4. Lưu vào lịch sử để Bot nhớ là mình vừa làm gì
                    save_history_to_memory(state["memory_db"], f"User: {user_input}")
                    save_history_to_memory(state["memory_db"], f"System Action: {final_answer}")

                    return # Giờ return mới an toàn

                elif intent == "WEB":
                    status_txt.value = "🌍 Đang tìm kiếm trên Internet..."
                    await page.update_async()
                    search_result = search_internet(user_input)
                    context_str = search_result
                    source_note = "\n\n*(Nguồn: Internet)*"

                elif intent == "MEMORY":
                    status_txt.value = "🧠 Đang lục lại ký ức..."
                    await page.update_async()
                    past_memories = search_memory(state["memory_db"], user_input)
                    if past_memories:
                        context_str = "\n\n".join(past_memories)
                        source_note = "\n\n*(Nguồn: Ký ức)*"
                    else:
                        context_str = "Không có ký ức liên quan."
                else:
                    status_txt.value = "💬 Đang soạn câu trả lời..."
                    await page.update_async()

                # STREAMING LLM
                spinner.visible = False
                msg_markdown = ft.Markdown("", extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
                bubble_container.content = ft.Column([
                    status_txt, # Giữ lại status text nhỏ ở trên
                    msg_markdown
                ])
                status_txt.value = f"✅ {intent} Mode" # Đổi status thành done
                status_txt.color = ft.colors.GREEN_400
                
                chunks = chain.stream({
                    "system_prompt": computer,
                    "context": context_str,
                    "input": user_input
                })

                full_response = ""
                for chunk in chunks:
                    full_response += chunk
                    msg_markdown.value = full_response + " ▌"
                    await page.update_async()
                
                final_answer = full_response + source_note
                msg_markdown.value = final_answer # Xóa con trỏ

            # --- SAVE & AUDIO ---
            if final_answer:
                save_history_to_memory(state["memory_db"], f"User: {user_input}")
                save_history_to_memory(state["memory_db"], f"Ai: {final_answer}")

                try:
                    lang = detect_language(final_answer)
                    audio_src = await generate_edge_audio(final_answer, lang)
                    audio_player.src = audio_src
                    audio_player.update()
                except: pass

        except Exception as e:
            spinner.visible = False
            bubble_container.content = ft.Text(f"❌ Lỗi: {str(e)}", color="red")
            await page.update_async()

    # --- FILE PICKER LOGIC ---
    # Khu vực hiển thị preview ảnh trước khi gửi
    preview_image = ft.Image(src="", width=50, height=50, fit=ft.ImageFit.COVER, border_radius=5)
    btn_clear_preview = ft.IconButton(ft.icons.CLOSE, icon_size=20, on_click=lambda e: clear_preview())
    
    preview_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.IMAGE, color=ft.colors.ORANGE),
            ft.Text("Ảnh đính kèm:", color=ft.colors.GREY_400),
            preview_image,
            btn_clear_preview
        ]),
        padding=10,
        bgcolor=ft.colors.GREY_900,
        border_radius=10,
        visible=False # Mặc định ẩn
    )

    def clear_preview():
        state["pending_image_path"] = None
        state["pending_image_bytes"] = None
        preview_container.visible = False
        page.update()

    async def on_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        file = e.files[0]
        ext = file.name.split('.')[-1].lower()

        # TRƯỜNG HỢP 1: ẢNH (Giao diện giống Messenger)
        if ext in ['jpg', 'jpeg', 'png', 'webp']:
            with open(file.path, "rb") as f:
                state["pending_image_bytes"] = f.read()
            state["pending_image_path"] = file.path
            
            # Hiển thị preview
            preview_image.src = file.path
            preview_container.visible = True
            input_box.focus()
            await page.update_async()

        # TRƯỜNG HỢP 2: TÀI LIỆU (Nạp kiến thức giống Streamlit)
        elif ext in ['pdf', 'txt']:
            # Tạo bong bóng thông báo hệ thống ngay lập tức
            sys_msg = ft.Row([
                ft.Icon(ft.icons.BOOK, color=ft.colors.PURPLE_400),
                ft.Text(f"Đang đọc tài liệu: {file.name}...", italic=True, color=ft.colors.PURPLE_200)
            ], alignment=ft.MainAxisAlignment.CENTER)
            chat_list.controls.append(sys_msg)
            await page.update_async()

            try:
                num_chunks = save_to_memory(state["memory_db"], file.path)
                chat_list.controls.append(
                    ft.Container(
                        content=ft.Text(f"✅ Đã học xong! ({num_chunks} phân đoạn)", color="green"),
                        alignment=ft.alignment.center
                    )
                )
            except Exception as ex:
                chat_list.controls.append(ft.Text(f"❌ Lỗi đọc file: {ex}", color="red"))
            await page.update_async()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    # --- INPUT LAYOUT ---
    async def btn_send_click(e):
        txt = input_box.value
        if not txt and not state["pending_image_bytes"]: return
        input_box.value = ""
        await process_message(txt, state["pending_image_bytes"], state["pending_image_path"])

    async def btn_mic_click(e):
        input_box.hint_text = "Đang nghe... 🎤"
        input_box.disabled = True
        await page.update_async()
        text = speech_to_text_mic()
        input_box.hint_text = "Nhập tin nhắn..."
        input_box.disabled = False
        if text: await process_message(text)
        else: await page.update_async()

    input_box = ft.TextField(
        hint_text="Nhập tin nhắn...",
        border_radius=30,
        expand=True,
        on_submit=btn_send_click,
        filled=True,
        bgcolor=ft.colors.GREY_900,
        border_color=ft.colors.TRANSPARENT,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=10)
    )

    # Thanh input bao gồm cả phần Preview ở trên
    input_area = ft.Container(
        content=ft.Column([
            preview_container, # Sẽ hiện lên khi chọn ảnh
            ft.Row([
                ft.IconButton(ft.icons.ATTACH_FILE, icon_color=ft.colors.GREY_400, on_click=lambda _: file_picker.pick_files()),
                input_box,
                ft.IconButton(ft.icons.MIC, icon_color=ft.colors.RED_400, on_click=btn_mic_click),
                ft.IconButton(ft.icons.SEND, icon_color=ft.colors.BLUE_400, on_click=btn_send_click),
            ])
        ]),
        padding=10,
        bgcolor=ft.colors.BLACK, # Nền đen để tách biệt
    )

    # Layout chính: Chat List ở trên, Input Area dính ở dưới
    main_layout = ft.Column(
        controls=[
            chat_list,
            ft.Divider(height=1, color=ft.colors.GREY_900), # Đường kẻ mờ ngăn cách
            input_area
        ],
        expand=True,
        spacing=0
    )

    # --- LOGIN ---
    pwd_input = ft.TextField(password=True, text_align="center", width=200, border_radius=20)
    async def check_login(e):
        if pwd_input.value == SECRET_PASSWORD:
            page.clean()
            page.add(main_layout)
            chat_list.controls.append(ft.Text("✨ ZERO đã sẵn sàng phục vụ!", color="orange", italic=True, text_align="center"))
            await page.update_async()
        else: pwd_input.error_text = "Sai mật khẩu!"
        await page.update_async()

    login_view = ft.Column([
        ft.Icon(ft.icons.SECURITY, size=60, color="blue"),
        ft.Text("ZERO SECURITY", size=20, weight="bold"),
        pwd_input,
        ft.ElevatedButton("ACCESS", on_click=check_login)
    ], alignment="center", horizontal_alignment="center")

    page.add(ft.Container(login_view, alignment=ft.alignment.center, expand=True))

if __name__ == "__main__":
    ft.app(target=main)