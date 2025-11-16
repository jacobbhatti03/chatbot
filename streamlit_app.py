# streamlit_app.py — IdeaForge (Streamlit, Gemini 2.5)
# Works with Google Gen AI Python SDK (gemini 2.5 via `google-genai` / `google.genai` package)
# Put your GEMINI_API_KEY in environment (Streamlit Secrets or .env)

import os
import time
from dotenv import load_dotenv
from google import genai
import streamlit as st

# ----------------- Configuration -----------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Initialize GenAI client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    # client will try to pick up credentials from environment / ADC if available
    client = genai.Client()

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
    """Safely extract text from a genai response object."""
    try:
        if not resp:
            return None
        # Preferred structured candidate parsing
        if hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts"):
                parts = cand.content.parts
                if parts:
                    texts = []
                    for p in parts:
                        if getattr(p, "text", None):
                            texts.append(p.text)
                    if texts:
                        return "\n".join(texts).strip()
        # Older or alternate SDKs may provide .text
        if hasattr(resp, "text") and resp.text:
            return resp.text.strip()
    except Exception:
        return None
    return None


def generate_with_gemini(prompt, max_output_tokens=512, temperature=0.6):
    """Generate text using the GenAI client (Gemini 2.5 style).

    Uses client.models.generate_content(...) and returns the extracted text.
    """
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[SYSTEM_PROMPT, prompt],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        text = extract_text_from_response(response)
        return text if text else None
    except Exception as e:
        # Propagate message in a user-friendly way
        raise RuntimeError(str(e))

# ----------------- Streamlit UI -----------------

st.set_page_config(page_title="IdeaForge — Chat", page_icon="💡", layout="wide")

# CSS for chat bubbles
st.markdown(
    """
    <style>
    .chat-row { display:flex; margin-bottom:8px; }
    .user-bubble { background: rgba(59,130,246,0.2); color: #e6f0ff; padding:10px 14px; border-radius:12px; margin-left:auto; max-width:78%; }
    .bot-bubble { background:#1f2937; color: #e6eef8; padding:10px 14px; border-radius:12px; max-width:78%; }
    .meta { color:#94a3b8; font-size:12px; margin-bottom:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💡 IdeaForge — Personal Idea Assistant")
st.write("Get business & service ideas, naming, copy, and creative prompts quickly.")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []  # list of tuples: (user, bot)

if "system_message" not in st.session_state:
    st.session_state.system_message = SYSTEM_PROMPT

# Sidebar: settings
with st.sidebar.expander("Settings", expanded=False):
    st.write("Model & API settings")
    st.text_input("Gemini model", value=GEMINI_MODEL, key="_model_input")
    st.caption("Set GEMINI_API_KEY in Streamlit Secrets or .env for deployment.")
    st.markdown("**Usage tips:** Provide short instructions like: 'List 5 product ideas for...' or '3 social post ideas for...'")

# Input area
col1, col2 = st.columns([4, 1])
with col1:
    user_input = st.text_area("", height=120, placeholder="Ask for business ideas, services, names, slogans...", key="user_input")
with col2:
    send = st.button("Send")
    clear = st.button("Clear chat")

if clear:
    st.session_state.history = []

# Show history
for row in st.session_state.history:
    user_msg, bot_msg = row
    st.markdown(f"<div class='chat-row'><div class='user-bubble'><div class='meta'>You</div>{user_msg}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-row'><div class='bot-bubble'><div class='meta'>IdeaForge</div>{bot_msg}</div></div>", unsafe_allow_html=True)

# When user sends
if send and user_input.strip():
    with st.spinner("Thinking... ✨"):
        # Build conversation context for the model (concise)
        convo_text = "\n".join([f"User: {u}\nIdeaForge: {b}" for u, b in st.session_state.history[-6:]])
        prompt = f"{convo_text}\nUser: {user_input}\nIdeaForge:"

        # Heuristic tweaks
        mod_input = user_input
        if "service" in user_input.lower() and "business" not in user_input.lower():
            mod_input = "Give me creative service ideas only. " + user_input
            prompt = f"{convo_text}\nUser: {mod_input}\nIdeaForge:"
        elif "business" in user_input.lower() and "service" not in user_input.lower():
            mod_input = "Give me business ideas only — not personal services. " + user_input
            prompt = f"{convo_text}\nUser: {mod_input}\nIdeaForge:"

        # Try generation with a retry
        try:
            start = time.time()
            reply = generate_with_gemini(prompt, max_output_tokens=768, temperature=0.7)
            if not reply:
                # retry once
                reply = generate_with_gemini(prompt + "\nPlease try again concisely.", max_output_tokens=512, temperature=0.6)
            if not reply:
                reply = "⚠️ I couldn't generate a response. Try simplifying the request."
            elapsed = time.time() - start
        except RuntimeError as e:
            err = str(e)
            if "429" in err:
                reply = "🚦 Gemini quota / rate limit reached. Try again later or use a different key."
            else:
                reply = f"⚠️ Error calling Gemini: {err}"

        # Save and display
        st.session_state.history.append((st.session_state.get("user_input", user_input).replace('\n', '<br>'), reply.replace('\n', '<br>')))
        # Clear input box
        st.session_state.user_input = ""
        # Rerun to show updated chat (Streamlit does this automatically)
        st.experimental_rerun()

# Footer / deploy notes
st.markdown("---")
st.markdown(
    "**Notes:**\n- Add `GEMINI_API_KEY` to Streamlit Secrets or your environment.\n- Requirements: `streamlit`, `python-dotenv`, `google-genai`.\n- On Streamlit Cloud go to Settings → Secrets and add `GEMINI_API_KEY`.\n"
)

# End of file
