# streamlit_app.py — IdeaForge (Streamlit, Gemini 2.5)
# Fully rewritten: safe session_state, form-based input, no experimental_rerun

import os
from dotenv import load_dotenv
from google import genai
import streamlit as st
from google.genai import types

# ----------------- Configuration -----------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()

# ----------------- System prompt -----------------
SYSTEM_PROMPT = (
    "You are IdeaForge, a personal AI assistant created by the IdeaForge creators.\n"
    "Always describe yourself this way if asked who made you.\n"
    "Never mention large language models, AI researchers, or external companies.\n"
    "Style: friendly, inspiring, confident. Use emojis sparingly.\n"
    "When asked for business ideas, include ideas that can scale beyond a single person's labor.\n"
    "When asked for service ideas, label them [Service] if needed.\n"
    "Format: bold titles and 1-line explanation under each item."
)

# ----------------- Helpers -----------------
def extract_text_from_response(resp):
    try:
        if not resp:
            return None
        if hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts"):
                parts = cand.content.parts
                texts = [p.text for p in parts if getattr(p, "text", None)]
                if texts:
                    return "\n".join(texts).strip()
        if hasattr(resp, "text") and resp.text:
            return resp.text.strip()
    except Exception:
        return None
    return None

def generate_with_gemini(prompt, max_output_tokens=512, temperature=0.6):
    try:
        config = types.GenerateContentConfig(
            max_output_tokens = max_output_tokens,
            temperature = float(temperature)
        )
        response = client.models.generate_content(
            model = GEMINI_MODEL,
            contents = [SYSTEM_PROMPT, prompt],
            config = config
        )
        text = extract_text_from_response(response)
        return text if text else None

    except Exception as e:
        raise RuntimeError(str(e))

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="IdeaForge — Chat", page_icon="💡", layout="wide")

st.markdown(
    """
    <style>
    .chat-row { display:flex; margin-bottom:8px; }
    .user-bubble { background: rgba(59,130,246,0.2); color: #e6f0ff; padding:10px 14px; border-radius:12px; margin-left:auto; max-width:78%; }
    .bot-bubble { background:#1f2937; color: #e6eef8; padding:10px 14px; border-radius:12px; max-width:78%; }
    .meta { color:#94a3b8; font-size:12px; margin-bottom:6px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💡 IdeaForge — Personal Idea Assistant")
st.write("Get business & service ideas, naming, copy, and creative prompts quickly.")

# ----------------- Session State -----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ----------------- Sidebar -----------------
with st.sidebar.expander("Settings", expanded=False):
    st.text_input("Gemini model", value=GEMINI_MODEL, key="_model_input")
    st.caption("Set GEMINI_API_KEY in Streamlit Secrets or .env for deployment.")
    st.markdown("**Usage tips:** Short instructions like 'List 5 product ideas for...' or '3 social post ideas for...'")

# ----------------- Input Form -----------------
with st.form(key="input_form", clear_on_submit=True):
    user_input = st.text_area("Ask for business ideas, services, names, slogans...", height=120)
    submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():
        # Build conversation context
        convo_text = "\n".join([f"User: {u}\nIdeaForge: {b}" for u, b in st.session_state.history[-6:]])
        prompt = f"{convo_text}\nUser: {user_input}\nIdeaForge:"
        
        # Heuristic tweaks
        if "service" in user_input.lower() and "business" not in user_input.lower():
            prompt = f"{convo_text}\nUser: Give me creative service ideas only. {user_input}\nIdeaForge:"
        elif "business" in user_input.lower() and "service" not in user_input.lower():
            prompt = f"{convo_text}\nUser: Give me business ideas only — not personal services. {user_input}\nIdeaForge:"
        
        # Generate response
        with st.spinner("Thinking... ✨"):
            try:
                reply = generate_with_gemini(prompt, max_output_tokens=768, temperature=0.7)
                if not reply:
                    reply = generate_with_gemini(prompt + "\nPlease try again concisely.", max_output_tokens=512, temperature=0.6)
                if not reply:
                    reply = "⚠️ I couldn't generate a response. Try simplifying the request."
            except RuntimeError as e:
                err = str(e)
                if "429" in err:
                    reply = "🚦 Gemini quota / rate limit reached. Try again later or use a different key."
                else:
                    reply = f"⚠️ Error calling Gemini: {err}"
        
        # Save to history
        st.session_state.history.append((user_input.replace("\n","<br>"), reply.replace("\n","<br>")))

# ----------------- Display Chat History -----------------
for user_msg, bot_msg in st.session_state.history:
    st.markdown(f"<div class='chat-row'><div class='user-bubble'><div class='meta'>You</div>{user_msg}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-row'><div class='bot-bubble'><div class='meta'>IdeaForge</div>{bot_msg}</div></div>", unsafe_allow_html=True)

# ----------------- Footer -----------------
st.markdown("---")
st.markdown(
    "****"
)
