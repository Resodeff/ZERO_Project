from gtts import gTTS
import tempfile
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import os
import io
import speech_recognition as sr
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from brain.hands import execute_action
from brain.router import classify_intent
from brain.tools import search_internet
from brain.vision import analyze_image
from brain.core import load_brain
from brain.personality import computer
from brain.memory import load_memory, save_to_memory, search_memory, save_history_to_memory

st.set_page_config(page_title="ZERO - Ai Companion", page_icon="✨")
st.title("ZERO ✨")

def speech_to_text(audio_bytes):
	r = sr.Recognizer()
	audio_data = sr.AudioFile(io.BytesIO(audio_bytes))

	with audio_data as source:
		audio = r.record(source)
		try:
			text = r.recognize_google(audio, language="vi-VN")
			return text
		except sr.UnknownValueError:
			return ""
		except sr.RequestError:
			st.error("Lỗi kết nối Google Speech API")
			return ""

def text_to_speech(text):
	try:
		tts = gTTS(text=text, lang='vi')
		with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
			temp_path = fp.name
			tts.save(temp_path)
		st.audio(temp_path, format="audio/mp3")
	except Exception as e:
		st.error(f"Lỗi âm thanh: {e}")

with st.sidebar:
	st.header("📂 Nạp kiến thức")
	uploaded_file = st.file_uploader("Chọn file PDF or TXT", type = ["pdf", "txt"])

	if uploaded_file is not None:
		if st.button("Học tài liệu này"):
			with st.spinner("Đang đọc và ghi nhớ..."):
				temp_path = f"./temp_{uploaded_file.name}"
				with open(temp_path, "wb") as f:
					f.write(uploaded_file.getbuffer())

				try:
					db = load_memory()
					num_chunks = save_to_memory(db, temp_path)
					st.success(f"Đã học xong! Tách thành {num_chunks} mảnh ký ức")
				except Exception as e:
					st.error(f"Lỗi: {e}")
				finally:
					if os.path.exists(temp_path):
						os.remove(temp_path)

	st.markdown("---")
	st.header("🎤 Nói chuyện")
	audio_input = mic_recorder(
		start_prompt = "Bấm để nói",
		stop_prompt = "Bấm để dừng",
		just_once = True,
		key = 'recorder',
		format = "wav"
		)
	st.markdown("---")
	st.header("📷 Gửi ảnh")
	uploaded_image = st.file_uploader("Chọn ảnh...", type=['ipg', 'jpeg', 'png'])

	if uploaded_image:
		st.image(uploaded_image, caption="Ảnh bạn gửi", use_container_width=True)

@st.cache_resource
def get_model():
	return load_brain()

@st.cache_resource
def get_memory_db():
	return load_memory()

llm = get_model()
memory_db = get_memory_db()

prompt_template = """
System: {system_prompt}

ký ức lên quan {thông tin từ quá khứ}: {context}

Human: {input}
"""

prompt = ChatPromptTemplate.from_messages([
	("system", "{system_prompt}"),
	("human", """
	thông tin ký ức (Memory): {context}
	human: {input}
	 """)
	])

chain = prompt | llm | StrOutputParser()

if "messages" not in st.session_state:
	st.session_state.messages = [
		{"role": "assistant", "content": "Chào bạn, mình là Aley. Chúc bạn một ngày tốt lành"}
	]

for msg in st.session_state.messages:
	with st.chat_message(msg["role"]):
		st.write(msg["content"])

user_final_input = None

if audio_input and audio_input['bytes']:
	speech_text = speech_to_text(audio_input['bytes'])
	if speech_text:
		user_final_input = speech_text
		st.session_state.messages.append({"role": "user", "content": user_final_input})
		with st.chat_message("user"):
			st.write(user_final_input)

if user_input := st.chat_input("Trò chuyện với Aley..."):
	user_final_input = user_input
	st.session_state.messages.append({"role": "user", "content": user_final_input})
	with st.chat_message("user"):
		st.write(user_final_input)

if user_final_input:
	final_answer = ""

	if uploaded_image:
		with st.chat_message("assistant"):
			with st.spinner("Aley đang nhìn ảnh..."):
				image_bytes = uploaded_image.getvalue()
				response = analyze_image(image_bytes, user_final_input)
				st.write(response)
				text_to_speech(response)

				final_answer = response
	else:
		with st.chat_message("assistant"):
			with st.spinner("Aley đang suy nghĩ..."):
				intent = classify_intent(user_final_input)

			if intent == "ACTION":
				st.caption("Quyết định hành động")
				with st.spinner("Đang thao tác..."):
					action_result = execute_action(user_final_input)
					final_answer = action_result

			if intent == "WEB":
				st.caption("🌐 Quyết định: Tìm kiếm Internet")
			elif intent == "MEMORY":
				st.caption("🧠 Quyết định: Tra cứu ký ức/Tài liệu")
			else:
				st.caption("💬 Quyết định: Trò chuyện logic")

			context_str = ""
			source_note = ""

			with st.spinner("Đang thực hiện..."):
				if intent == "WEB":
					search_result = search_internet(user_final_input)
					context_str = search_result
					source_note = "\n\n(Tìm thấy từ Internet)"
				elif intent == "MEMORY":
					past_memories = search_memory(memory_db, user_final_input)
					if past_memories:
						context_str = "\n\n".join(past_memories)
						source_note = "\n\n(Trích xuất từ ký ức)"
					else:
						context_str = "Không tìm thấy trong bộ nhớ"
				else:
					context_str = "Không cần thông tin bên ngoài"
					source_note = ""

				full_response = chain.invoke({
					"system_prompt": computer,
					"context": context_str,
					"input": user_final_input
				})

				final_answer = full_response + source_note

				st.write(final_answer)
				text_to_speech(final_answer)

	if final_answer:
		st.session_state.messages.append({"role": "assistant", "content": final_answer})
		save_history_to_memory(memory_db, final_answer)