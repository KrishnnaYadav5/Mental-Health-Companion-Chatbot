import streamlit as st
import requests

# -------------------- CONFIG -------------------- 

st.set_page_config(
    page_title="Student Wellness Companion",
    page_icon="🌱",
    layout="centered",
)

# UPDATED FOR 2026: Using the Gemini 3 Flash model
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash:generateContent"

SYSTEM_INSTRUCTION = """
You are a compassionate and supportive AI companion designed specifically for students.
Your primary role is to provide emotional support, detect mood, and respond with empathy.
Validate feelings first, suggest relaxation techniques when needed, and follow safety protocols.
Keep responses warm and concise. 🌟💚
"""

# -------------------- HELPERS --------------------

def call_gemini(api_key: str, history, user_message: str) -> str:
    """Communicates with the Gemini 3 API via REST."""
    contents = []
    
    # Requirement: The conversation MUST start with a 'user' message.
    # We skip the initial assistant greeting from the session state history.
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
        # We append the key to the URL as a query parameter
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        
        # Handle the specific 404/403 errors with clear feedback
        if resp.status_code == 404:
            raise RuntimeError("Model 'gemini-3-flash' not found. Please check your API project in Google AI Studio.")
        
        resp.raise_for_status()
        data = resp.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return "I'm listening, but I couldn't generate a response. Mind trying again?"

    except requests.exceptions.HTTPError as e:
        error_info = resp.json().get("error", {}).get("message", str(e))
        raise RuntimeError(f"API Error: {error_info}")
    except Exception as e:
        raise RuntimeError(f"Connection Error: {e}")

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
    if st.button("🔑 Reset API Key"):
        st.session_state.api_key = None
        st.rerun()

st.title("Student Wellness Companion")

# -------------------- API KEY ENTRY --------------------

if not st.session_state.api_key:
    st.info("Welcome! Please enter your Gemini API Key from Google AI Studio to begin.")
    key = st.text_input("API Key", type="password", placeholder="Paste your key here...")
    if st.button("Connect"):
        if key:
            st.session_state.api_key = key
            st.rerun()
        else:
            st.error("API Key is required.")
    st.stop()

# -------------------- CHAT LOGIC --------------------

# Initial Assistant Greeting
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hey there! 👋 I'm your Wellness Companion. How's your day going? 💚"
    })

# Display Chat History
for msg in st.session_state.messages:
    avatar = "😊" if msg["role"] == "user" else "🌱"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# User Chat Input
if prompt := st.chat_input("Tell me what's on your mind..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="😊"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Thinking with care..."):
            try:
                # Pass previous history (excluding the greeting if necessary is handled in call_gemini)
                reply = call_gemini(st.session_state.api_key, st.session_state.messages[:-1], prompt)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Something went wrong: {e}")
