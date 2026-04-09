import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import base64
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="SmartStudyApp", page_icon="🎓", layout="wide")

# --- INITIALIZATION ---
try:
    # Safely pulling the key from your Streamlit Secrets
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.warning("API Key not found in Secrets. Please add GOOGLE_API_KEY to your Streamlit dashboard.")
except Exception as e:
    st.error(f"Configuration error: {e}")

if "messages" not in st.session_state: st.session_state.messages = []
if "profile" not in st.session_state: st.session_state.profile = None
if "usage_count" not in st.session_state: st.session_state.usage_count = 0
if "max_limit" not in st.session_state: st.session_state.max_limit = 15 

# Correct model initialization for Gemini Pro
model = genai.GenerativeModel('gemini-pro')

# --- COVER PAGE ---
if st.session_state.profile is None:
    st.title("🎓 SmartStudyApp")
    st.subheader("Your AI-Powered Study Companion")
    st.markdown("---")
    st.markdown("### Welcome, Student!")
    st.markdown("**Created by: Christiana Joseph Ugochukwu** | *Proudly built for the 3MTT Program*")
    st.markdown("---")
    
    with st.form("profile_form"):
        name = st.text_input("Enter your name:")
        exam = st.selectbox("Select your exam or course:", 
                           ["Common Entrance", "Junior WAEC (BECE)", "JAMB", "WAEC", 
                            "Professional Course: Data Science", "Professional Course: Web Dev"])
        code = st.text_input("Access Code (If applicable):", type="password")
        if st.form_submit_button("Start Learning"):
            if name:
                st.session_state.profile = {"name": name, "exam": exam}
                if code == "JUDGE2026": st.session_state.max_limit = 50
                st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"Hi, {st.session_state.profile['name']}! 👋")
st.sidebar.write(f"**Target Exam:** {st.session_state.profile['exam']}")
st.sidebar.write(f"**Usage:** {st.session_state.usage_count} / {st.session_state.max_limit} used.")

st.sidebar.markdown("### 📂 Study Materials")
st.sidebar.file_uploader("Upload your PDF notes here:", type=["pdf"])

with st.sidebar.expander("⚙️ Settings"):
    creativity = st.slider("Creativity Level", 0.0, 1.0, 0.7)
    lang = st.selectbox("Response Language", ["English", "Igbo", "Hausa", "Yoruba"])
    speed = st.selectbox("Speech Speed", ["Normal", "Slow"])

with st.sidebar.expander("❓ Help & Tips"):
    st.write("1. Upload PDF notes to study.")
    st.write("2. Click '🔊 Listen' to hear responses.")
    st.write("3. Keep questions clear and concise.")

if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.session_state.usage_count = 0
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Created by: Christiana Joseph Ugochukwu - 3MTT Project")

# --- MAIN CHAT AREA ---
st.title("📚 SmartStudyApp")

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            if st.button("🔊 Listen", key=f"btn_{i}"):
                with st.spinner("Generating audio..."):
                    try:
                        tts = gTTS(text=m["content"], lang='en', slow=(speed == "Slow"))
                        temp_file = f"audio_{i}.mp3"
                        tts.save(temp_file)
                        with open(temp_file, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
                        os.remove(temp_file)
                    except Exception:
                        st.error("Audio service temporarily unreachable.")

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask your tutor a question..."):
    if st.session_state.usage_count >= st.session_state.max_limit:
        st.error("Limit reached. Please upgrade to Pro.")
    else:
        st.session_state.usage_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # Correct way to generate content with the GenerativeModel
                response = model.generate_content(
                    contents=f"You are a helpful {st.session_state.profile['exam']} tutor. Answer in {lang}: {prompt}",
                    generation_config={"temperature": creativity}
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Error generating response: {e}")
