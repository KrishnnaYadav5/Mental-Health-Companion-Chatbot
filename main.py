import streamlit as st
import requests

# -------------------- CONFIG -------------------- 

st.set_page_config(
    page_title="Student Wellness Companion",
    page_icon="🌱",
    layout="centered",
)

# Use gemini-1.5-flash for the standard production endpoint
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"

SYSTEM_INSTRUCTION = """
You are a compassionate and supportive AI companion designed specifically for students.
Your primary role is to provide emotional support, detect mood, and respond with empathy.
Keep responses concise, use gentle emojis, and follow safety protocols for distress.
"""

# -------------------- HELPERS --------------------

def call_gemini(api_key: str, history, user_message: str) -> str:
    """Sends chat history to Gemini API via REST and returns the response."""
    contents = []
    
    # Logic Fix: Gemini API requires the conversation to start with a 'user' message.
    # We skip any initial 'assistant' greeting messages in the history payload.
    for msg in history:
        if not contents and msg["role"] == "assistant":
            continue
            
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    # Add the current user message
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
        resp.raise_for_status()
        data = resp.json()
        
        # Extract response text
        return data["candidates"][0]["content"]["parts"][0]["text"]
        
    except requests.exceptions.HTTPError as e:
        try:
            # Try to grab the specific error message from Google (e.g., "Invalid API Key")
            msg = resp.json().get("error", {}).get("message", str(e))
        except:
            msg = str(e)
        raise RuntimeError(f"API Error: {msg}")
    except Exception as e:
        raise RuntimeError(f"Connection Error: {e}")

# -------------------- SESSION STATE --------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = None

# -------------------- SIDEBAR & UI --------------------

with st.sidebar:
    st.title("Settings & Tips")
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔑 Reset API Key"):
        st.session_state.api_key = None
        st.rerun()
    
    st.divider()
    st.markdown("### 🧘 Quick Tips")
    st.info("4-7-8 Breathing: Inhale 4s, Hold 7s, Exhale 8s.")

st.title("🌱 Student Wellness Companion")

# -------------------- API KEY ENTRY --------------------

if not st.session_state.api_key:
    key_input = st.text_input("Enter Gemini API Key", type="password")
    if st.button("Connect"):
        if key_input:
            st.session_state.api_key = key_input
            st.rerun()
        else:
            st.error("Please enter a key.")
    st.stop()

# -------------------- CHAT LOGIC --------------------

# Greeting
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hey! I'm your Wellness Companion. How are you feeling today? 💚"
    })

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Tell me what's on your mind..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = call_gemini(st.session_state.api_key, st.session_state.messages[:-1], prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Something went wrong: {e}")
