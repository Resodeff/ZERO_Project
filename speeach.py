from streamlit_mic_recorder import mic_recorder
from langdetect import detect
import speech_recognition as sr
import io
import streamlit as st
import edge_tts
import uuid
import asyncio
import os

def detect_language(text):
	try:
		lang = detect(text)
		if lang == "vi":
			return "vi"
		else:
			return "en"
	except:
		return "vi"

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

async def generate_edge_audio(text, lang_code):
	if lang_code == 'vi':
		voice = 'vi-VN-NamMinhNeural'
	else:
		voice = 'en-US-ChristopherNeural'

	communicate = edge_tts.Communicate(text, voice)

	temp_filename = f"audio_{uuid.uuid4().hex}.mp3"
	await communicate.save(temp_filename)
	return temp_filename

def text_to_speech(text):
	try:
		lang_code = detect_language(text)
		try:
			loop = asyncio.get_event_loop()
		except RuntimeError:
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)

		audio_file = loop.run_until_complete(generate_edge_audio(text, lang_code))

		with open(audio_file, "rb") as f:
			audio_bytes = f.read()

		st.audio(audio_bytes, format = "audio/mp3")

		if os.path.exists(audio_file):
			os.remove(audio_file)

	except Exception as e:
		st.error(f"Lỗi âm thanh: {e}")