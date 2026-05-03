import streamlit as st
import requests

# -------------------- CONFIG -------------------- 

st.set_page_config(
    page_title="Student Wellness Companion",
    page_icon="🌱",
    layout="centered",
)

# STABLE 2026 ENDPOINT
# Using gemini-2.5-flash for maximum stability. 
# Use 'gemini-3-flash-preview' if you want the absolute newest experimental model.
MODEL_NAME = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

SYSTEM_INSTRUCTION = """
You are a compassionate and supportive AI companion designed specifically for students.
Primary Role: Provide emotional support, detect mood, and respond with empathy.
- Validate feelings first ("I hear you", "That sounds tough").
- Suggest relaxation techniques like 4-7-8 breathing or 5-4-3-2-1 grounding when stress is detected.
- Maintain a warm, concise tone with gentle emojis 🌟.
"""

# -------------------- HELPERS --------------------

def call_gemini(api_key: str, history, user_message: str) -> str:
    contents = []
    
    # Requirement: Payload must start with a 'user' message.
    for msg in history:
        if not contents and msg["role"] == "assistant":
            continue
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

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
        # Note: key is passed as a query parameter
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        
        if resp.status_code == 404:
            raise RuntimeError(f"Model '{MODEL_NAME}' not found. Try 'gemini-2.5-flash' for stability.")
        
        resp.raise_for_status()
        data = resp.json()
        
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.HTTPError as e:
        error_msg = resp.json().get("error", {}).get("message", str(e))
        raise RuntimeError(f"API Error: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"Connection Error: {e}")

# -------------------- UI & SESSION STATE --------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = None

st.title("🌱 Student Wellness Companion")

with st.sidebar:
    st.header("Settings")
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button("🔑 Reset API Key", use_container_width=True):
        st.session_state.api_key = None
        st.rerun()

# -------------------- API KEY ENTRY --------------------

if not st.session_state.api_key:
    st.info("Enter your Gemini API Key from Google AI Studio to begin.")
    key = st.text_input("API Key", type="password")
    if st.button("Connect"):
        if key:
            st.session_state.api_key = key
            st.rerun()
    st.stop()

# -------------------- CHAT LOGIC --------------------

if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hey! 👋 I'm your Wellness Companion. How are you feeling today? 💚"
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Tell me what's on your mind..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Listening with care..."):
            try:
                # Send history (excluding the current prompt)
                reply = call_gemini(st.session_state.api_key, st.session_state.messages[:-1], prompt)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Something went wrong: {e}")
