import streamlit as st
import requests

# -------------------- CONFIG -------------------- 

st.set_page_config(
    page_title="Student Wellness Companion",
    page_icon="🌱",
    layout="centered",
)

# Use the v1beta endpoint to support 'system_instruction'
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SYSTEM_INSTRUCTION = """
You are a compassionate and supportive AI companion designed specifically for students.
Your primary role is to provide emotional support, detect mood, and respond with empathy.

Core Behaviors:
1. Mood Detection: Identify stress, anxiety, or positive emotions.
2. Empathetic Responses: Always validate feelings first.
3. Motivational Support: Offer tailored encouragement.
4. Relaxation Tips: Suggest deep breathing (4-7-8) or grounding (5-4-3-2-1) when stressed.
5. Safety Protocol: If severe distress is detected, provide crisis helpline info immediately.

Response Style:
- Keep responses concise but warm.
- Use gentle emojis occasionally 🌟💚.
- Ask follow-up questions to show care.
"""

# -------------------- HELPERS --------------------

def call_gemini(api_key: str, history, user_message: str) -> str:
    """Communicates with Gemini via REST API."""
    contents = []
    
    # CRITICAL: Gemini API requires the conversation to start with a 'user' role.
    # We filter out the initial assistant greeting from the payload sent to Google.
    for msg in history:
        if not contents and msg["role"] == "assistant":
            continue
            
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    # Add the newest user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}],
    })

    # Construct the JSON payload
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
        
        # Handle HTTP errors
        if resp.status_code != 200:
            error_data = resp.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown API error")
            raise RuntimeError(f"Gemini API Error ({resp.status_code}): {error_msg}")
            
        data = resp.json()
        
        # Extract text from the response
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "I'm here and listening, but I couldn't generate a response. Could you tell me more?"

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection failed: {str(e)}")

# -------------------- SESSION STATE --------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = None

# -------------------- UI: SIDEBAR --------------------

with st.sidebar:
    st.title("🌱 Companion Settings")
    
    if st.button("🔄 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔑 Reset API Key", use_container_width=True):
        st.session_state.api_key = None
        st.rerun()

    st.divider()
    
    with st.expander("🧘 Relaxation Techniques"):
        st.markdown("**4-7-8 Breathing**")
        st.caption("Inhale 4s, Hold 7s, Exhale 8s.")
        st.markdown("**5-4-3-2-1 Grounding**")
        st.caption("Identify 5 things you see, 4 you feel...")

    st.divider()
    st.markdown("### 📞 Crisis Help")
    st.info("US: 988\n\nIndia: 9152987821")

# -------------------- API KEY ENTRY --------------------

if not st.session_state.api_key:
    st.title("Welcome! ✨")
    st.write("To begin your wellness journey, please enter your Gemini API Key.")
    
    key_input = st.text_input("API Key", type="password", help="Get a free key at aistudio.google.com")
    
    if st.button("Connect Companion", type="primary"):
        if key_input:
            st.session_state.api_key = key_input
            st.success("Connected! Starting session...")
            st.rerun()
        else:
            st.warning("Please provide a valid key.")
    st.stop()

# -------------------- CHAT INTERFACE --------------------

st.title("Student Wellness Companion")

# Initialize greeting if empty
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hey! 👋 I'm here for you. Whether it's study stress or just a long day, how are you feeling? 💚"
    })

# Display message history
for msg in st.session_state.messages:
    avatar = "😊" if msg["role"] == "user" else "🌱"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# User Chat Input
if prompt := st.chat_input("Tell me what's on your mind..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="😊"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Listening with care..."):
            try:
                # Pass all history except the one we just added to avoid duplication
                response = call_gemini(st.session_state.api_key, st.session_state.messages[:-1], prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Something went wrong: {e}")
