import streamlit as st
import requests

# -------------------- CONFIG -------------------- 

st.set_page_config(
    page_title="Student Wellness Companion",
    page_icon="🌱",
    layout="centered",
)

# FIXED: Changed model name to gemini-1.5-flash (standard production name)
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"

SYSTEM_INSTRUCTION = """
You are a compassionate and supportive AI companion designed specifically for students.
Your primary role is to provide emotional support, detect mood, and respond with empathy.
(Keep responses concise, use gentle emojis, and follow safety protocols.)
"""

# -------------------- HELPERS --------------------

def call_gemini(api_key: str, history, user_message: str) -> str:
    contents = []
    
    # FIXED: The Gemini API requires the FIRST message to be from the 'user'.
    # We filter the history to ensure we don't start with an 'assistant' message.
    for msg in history:
        # Skip the very first message if it's from the assistant
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
        
        # Extract text response
        candidates = data.get("candidates", [])
        if not candidates:
            return "I'm listening, but I couldn't process that. Can you try rephrasing?"
            
        return candidates[0]["content"]["parts"][0]["text"]
        
    except requests.exceptions.HTTPError as e:
        # Check for 401 (Invalid Key) or 404 (Model Name error)
        try:
            err_details = resp.json().get("error", {}).get("message", str(e))
        except:
            err_details = str(e)
        raise RuntimeError(f"API Error: {err_details}")
    except Exception as e:
        raise RuntimeError(f"Connection Error: {e}")

# ... (Rest of your UI and Session State code remains the same) ...
