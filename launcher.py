import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

import flet as ft
import subprocess
import json
import os
import threading
import sys
import time

AVAILABLE_MODELS = [
    {"name": "Gemma 2B (Google)", "id": "gemma:2b", "desc": "Siêu nhẹ (RAM 4GB). Chạy nhanh, trả lời ngắn gọn.", "color": "green"},
    {"name": "Qwen 1.5B (Alibaba)", "id": "qwen2:1.5b", "desc": "Nhẹ, hỗ trợ Tiếng Việt & Code tốt.", "color": "blue"},
    {"name": "Llama 3 (Meta)", "id": "llama3", "desc": "Thông minh nhất (RAM 8GB+). Cần máy khỏe.", "color": "purple"},
    {"name": "Mistral (Pháp)", "id": "mistral", "desc": "Cân bằng giữa tốc độ và trí tuệ.", "color": "orange"},
]

CONFIG_FILE = "config.json"

def main(page: ft.Page):
    page.title = "ZERO AI - Launcher"
    page.window_width = 500
    page.window_height = 650
    page.window_resizable = False
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    def get_installed_models():
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, encoding='utf-8', shell=True)
            return result.stdout
        except FileNotFoundError:
            return ""

    def save_config(model_id):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"selected_model": model_id}, f)

    def download_model(model_id, progress_bar, status_text, start_btn):
        status_text.value = f"Đang tải {model_id}... Vui lòng đợi."
        status_text.color = "yellow"
        progress_bar.visible = True
        page.update()

        try:
            subprocess.run(["ollama", "pull", model_id], check=True, shell=True)
            status_text.value = f"Đã tải xong {model_id}! Hãy chọn lại."
            status_text.color = "green"
        except Exception as e:
            status_text.value = f"Lỗi tải: {e}"
            status_text.color = "red"
        
        progress_bar.visible = False
        update_list() 
        page.update()

    def launch_zero(e):
        launch_btn.text = "ĐANG KHỞI ĐỘNG..."
        launch_btn.disabled = True
        page.update()

        current_dir = os.getcwd()
        portable_python = os.path.join(current_dir, "python_env", "python.exe")
        app_path = os.path.join(current_dir, "app", "app.py")

        try:
            if os.path.exists(portable_python):
                print("Đang chạy chế độ Portable...")
                cmd = [portable_python, "-m", "streamlit", "run", app_path]
                subprocess.Popen(cmd, cwd=current_dir)
            else:
                print("Không thấy Portable, chạy chế độ System...")
                subprocess.Popen(["streamlit", "run", "app.py"], shell=True)
            
            time.sleep(2)
            page.window_destroy()

        except Exception as ex:
            launch_btn.text = f"LỖI: {str(ex)}"
            page.update()

    header = ft.Text("ZERO SETUP", size=30, weight="bold", text_align="center")
    sub_header = ft.Text("Chọn bộ não phù hợp với máy của bạn", color="grey")
    
    status_text = ft.Text("", size=12)
    progress_bar = ft.ProgressBar(visible=False, color="blue")
    
    model_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=350)

    launch_btn = ft.ElevatedButton(
        "KHỞI ĐỘNG ZERO 🚀", 
        width=400, height=50, 
        bgcolor="blue", color="white",
        disabled=True,
        on_click=launch_zero 
    )

    def select_model(model_id):
        save_config(model_id)
        launch_btn.disabled = False
        launch_btn.text = f"KHỞI ĐỘNG VỚI {model_id.upper()} 🚀"
        launch_btn.bgcolor = "green"
        page.update()

    def update_list():
        model_column.controls.clear()
        installed = get_installed_models()

        if not installed:
            status_text.value = "Cảnh báo: Không tìm thấy Ollama! Hãy cài đặt Ollama trước."
            status_text.color = "red"

        for m in AVAILABLE_MODELS:
            is_installed = m["id"] in installed
            
            if is_installed:
                btn = ft.ElevatedButton("Chọn", on_click=lambda e, mid=m["id"]: select_model(mid))
                icon = ft.Icon(ft.icons.CHECK_CIRCLE, color="green")
            else:
                btn = ft.OutlinedButton("Tải về", on_click=lambda e, mid=m["id"]: threading.Thread(target=download_model, args=(mid, progress_bar, status_text, launch_btn)).start())
                icon = ft.Icon(ft.icons.DOWNLOAD, color="grey")

            card = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.MEMORY, color=m["color"]),
                    ft.Column([
                        ft.Text(m["name"], weight="bold"),
                        ft.Text(m["desc"], size=10, color="grey"),
                    ], expand=True),
                    btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10,
                border=ft.border.all(1, "grey" if not is_installed else m["color"]),
                border_radius=10,
                bgcolor=ft.colors.BLACK38
            )
            model_column.controls.append(card)
        page.update()

    page.add(
        ft.Column([
            header, sub_header, 
            ft.Divider(),
            status_text, progress_bar,
            model_column,
            ft.Divider(),
            launch_btn
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    update_list()

ft.app(target=main)