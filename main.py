import streamlit as st
import requests

# -------------------- CONFIG -------------------- 

st.set_page_config(
    page_title="Student Wellness Companion",
    page_icon="🌱",
    layout="centered",
)

# FIXED: Added '-latest' to the model name which often resolves the 404 error
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

SYSTEM_INSTRUCTION = """
You are a compassionate and supportive AI companion designed specifically for students.
Your primary role is to provide emotional support, detect mood, and respond with empathy.
Validate feelings first, suggest relaxation techniques (4-7-8 breathing) when needed, 
and provide crisis info if severe distress is detected. 🌟💚
"""

# -------------------- HELPERS --------------------

def call_gemini(api_key: str, history, user_message: str) -> str:
    """Communicates with Gemini via REST API."""
    contents = []
    
    # Filter history to ensure we start with a 'user' message
    for msg in history:
        if not contents and msg["role"] == "assistant":
            continue
            
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    # Add current user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}],
    })

    payload = {
        "contents": contents,
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION.strip()}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }
    
    try:
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        
        # If the -latest alias fails, we catch it here
        if resp.status_code == 404:
            raise RuntimeError("Model path not found. Try checking your API permissions in AI Studio.")
            
        resp.raise_for_status()
        data = resp.json()
        
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return "I'm listening, but couldn't quite process that. Try again?"

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")

# -------------------- SESSION STATE --------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = None

# -------------------- UI --------------------

with st.sidebar:
    st.title("🌱 Settings")
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    if st.button("🔑 Reset Key"):
        st.session_state.api_key = None
        st.rerun()

st.title("Student Wellness Companion")

# -------------------- API KEY ENTRY --------------------

if not st.session_state.api_key:
    st.info("Enter your Gemini API Key from [Google AI Studio](https://aistudio.google.com/) to begin.")
    key = st.text_input("API Key", type="password")
    if st.button("Connect"):
        if key:
            st.session_state.api_key = key
            st.rerun()
    st.stop()

# -------------------- CHAT LOGIC --------------------

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "Hey! 👋 How are you feeling today? 💚"})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Listening..."):
            try:
                reply = call_gemini(st.session_state.api_key, st.session_state.messages[:-1], prompt)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(str(e))
