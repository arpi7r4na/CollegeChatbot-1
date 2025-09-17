import os
import base64
from io import BytesIO
import sqlite3

import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="College Voice Chatbot", page_icon="🎓", layout="centered")

# --- Load API Key ---
API_KEY = "AIzaSyBI8eySy9C69NORGrzU8vSvhDu06Wb0bdk"  # Replace with your Gemini API key
genai.configure(api_key=API_KEY)
if not API_KEY:
    st.error("Gemini API key missing. Set it properly.")
    st.stop()

# --- Load FAQ Data ---
faq_df = pd.read_csv("faqs.csv")

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'student_name' not in st.session_state:
    st.session_state.student_name = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_prompt' not in st.session_state:
    st.session_state.last_prompt = None
if 'selected_language_name' not in st.session_state:
    st.session_state.selected_language_name = 'English'
if 'selected_language_code' not in st.session_state:
    st.session_state.selected_language_code = 'en'
if 'voice_input' not in st.session_state:
    st.session_state.voice_input = None
if 'show_timetable' not in st.session_state:
    st.session_state.show_timetable = False
if 'language_changed' not in st.session_state:
    st.session_state.language_changed = False  # NEW FLAG

# --- Helper Functions ---
def verify_login(username, password):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def get_student_data(username):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, fee_status, course FROM students WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"name": result[0], "fee_status": result[1], "course": result[2]}
    return None

def get_course_timetable(course):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT day, schedule FROM timetables WHERE course=?", (course,))
    rows = cursor.fetchall()
    conn.close()
    timetable = {day: schedule for day, schedule in rows}
    return timetable

def transcribe_audio(audio_bytes: bytes) -> str | None:
    if not audio_bytes:
        return None
    recognizer = sr.Recognizer()
    audio_io = BytesIO(audio_bytes)
    try:
        seg = AudioSegment.from_file(audio_io)
        wav_io = BytesIO()
        seg.export(wav_io, format="wav")
        wav_io.seek(0)
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language=st.session_state.selected_language_code)
    except sr.UnknownValueError:
        st.warning("Could not understand the audio. Please try again.")
        return None
    except Exception as e:
        st.error(f"Audio processing failed. Ensure FFmpeg is installed. Details: {e}")
        return None

def text_to_audio_autoplay(text: str, lang_code: str) -> str | None:
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        b64 = base64.b64encode(audio_bytes.read()).decode()
        return f'<audio autoplay controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        return None

def get_bot_response(user_query, language_name, language_code, student_data):
    faq_text = '\n'.join([f'{q}: {a}' for q, a in zip(faq_df['question'], faq_df['answer'])])
    student_timetable = get_course_timetable(student_data['course'])
    timetable_text = '\n'.join([f'{day}: {schedule}' for day, schedule in student_timetable.items()])

    system_instruction = f"""
You are a helpful and polite college chatbot assistant.

Student Info:
- Name: {student_data['name']}
- Fee Status: {student_data['fee_status']}
- Course: {student_data['course']}

General FAQs:
{faq_text}

Student Timetable:
{timetable_text}

CRITICAL RULES:
1. The user's preferred language is {language_name}.
2. Understand the user's query regardless of the language.
3. Reply ONLY in {language_name}.
4. Keep answers concise.
5. Do not provide information about other students.
6. If the user asks for full timetable, reply that they can see it via the Timetable button.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
        resp = model.generate_content(user_query)
        return (resp.text or '').strip() or '…'
    except Exception as e:
        st.error(f"❌ Error contacting AI model: {e}")
        return "Sorry, I encountered an error."

# --- LOGIN PAGE ---
if not st.session_state.logged_in:
    st.title("🎓 Student Login")
    with st.form(key='login_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        submit_button = st.form_submit_button("Login")

        if submit_button:
            student_name = verify_login(username, password)
            if student_name:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.student_name = student_name
                st.stop()
            else:
                st.error("Invalid username or password.")

# --- CHATBOT PAGE ---
else:
    st.title(f"🎓 Welcome {st.session_state.student_name}")
    student_data = get_student_data(st.session_state.username)

    # --- Sidebar Controls ---
    with st.sidebar:
        st.header("⚙️ Controls")
        languages = {
            "English": "en", "Hindi (हिन्दी)": "hi", "Punjabi (ਪੰਜਾਬੀ)": "pa",
            "Gujarati (ગુજરાતી)": "gu", "Marwari (मारवाड़ी)": "hi", "Marathi (मराठी)": "mr",
            "Bengali (বাংলা)": "bn", "Kannada (ಕನ್ನಡ)": "kn", "Tamil (தமிழ்)": "ta",
            "German (Deutsch)": "de", "French (Français)": "fr", "Spanish (Español)": "es", "Russian (Русский)": "ru",
        }

        selected_language_name = st.selectbox(
            "Choose your language:",
            options=list(languages.keys()),
            index=list(languages.keys()).index(st.session_state.selected_language_name)
        )
        selected_language_code = languages[selected_language_name]

        # --- Update language without replaying last prompt ---
        if selected_language_name != st.session_state.selected_language_name:
            st.session_state.selected_language_name = selected_language_name
            st.session_state.selected_language_code = selected_language_code
            st.session_state.language_changed = True  # NEW FLAG

        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []

        # --- Timetable Button ---
        if st.button("🗓️ Show/Hide Timetable"):
            st.session_state.show_timetable = not st.session_state.show_timetable

        if st.session_state.show_timetable:
            student_timetable = get_course_timetable(student_data['course'])
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            all_slots = set()
            timetable_data = {}
            for day, schedule in student_timetable.items():
                if schedule.lower() == "holiday":
                    timetable_data[day] = ["Holiday"]
                    continue
                slots = [s.strip() for s in schedule.split(",")]
                timetable_data[day] = slots
                for s in slots:
                    time_range = s.split(":")[0].strip()
                    all_slots.add(time_range)
            all_slots = sorted(all_slots)

            grid_data = []
            for day in days_order:
                row = []
                if timetable_data[day][0] == "Holiday":
                    row = ["Holiday"] * len(all_slots)
                else:
                    subjects_dict = {}
                    for s in timetable_data[day]:
                        time, subject = s.split(":", 1)
                        subjects_dict[time.strip()] = subject.strip()
                    row = [subjects_dict.get(t, "") for t in all_slots]
                grid_data.append(row)

            timetable_df = pd.DataFrame(grid_data, index=days_order, columns=all_slots)
            st.markdown("### 📅 Your Weekly Timetable")
            st.table(timetable_df)

        st.markdown("---")
        st.markdown("##### 🎙️ Voice Input")
        voice_input = mic_recorder(start_prompt="🎙️ Speak now...", stop_prompt="⏹️ Stop", key="voice_recorder_sidebar")
        if voice_input and voice_input.get("bytes"):
            st.session_state.voice_input = voice_input["bytes"]

    # --- Render Chat History ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Determine Prompt ---
    prompt = None
    if st.session_state.voice_input:
        prompt = transcribe_audio(st.session_state.voice_input)
        st.session_state.voice_input = None

    text_prompt = st.chat_input("Type your question here…")
    if text_prompt:
        prompt = text_prompt

    # --- Main Chat Logic ---
    if prompt:
        # Skip if language was just changed
        if st.session_state.get("language_changed", False):
            st.session_state.language_changed = False
        else:
            if st.session_state.get("last_prompt") != prompt:
                st.session_state.last_prompt = prompt

                # User message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Bot response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        reply = get_bot_response(
                            prompt,
                            st.session_state.selected_language_name,
                            st.session_state.selected_language_code,
                            student_data
                        )
                        st.markdown(reply)

                        audio_html = text_to_audio_autoplay(reply, st.session_state.selected_language_code)
                        if audio_html:
                            st.markdown(audio_html, unsafe_allow_html=True)

                st.session_state.messages.append({"role": "assistant", "content": reply})
