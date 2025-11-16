#💡 IDEA FORGE — Clean, Fast, and Safe Version
# Works perfectly in Colab or Hugging Face
# Author: You 🚀

import os
import time
import threading
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv

# ---- Configure Gemini ----
# 👇 Add your Gemini API key here or through environment variable
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # Fast + Free-tier friendly

# ---- System Prompt ----
SYSTEM_PROMPT = """
You are IdeaForge, a personal AI assistant created by the IdeaForge creators.
Always describe yourself this way if asked who made you.
Never mention large language models, AI researchers, or external companies.
✨ Style Guidelines:
- Be friendly, inspiring, and confident.
- Use emojis sparingly (1–2 per point) to make answers feel alive.
🧠 Important Rule:
- When asked for *business ideas*, list ideas that involve a product, brand, or company that generates profit beyond one person’s labor.
- When asked for *service ideas*, list ideas that involve providing help, expertise, or time directly to clients.
- If unsure, clearly label ideas as **[Service]** or **[Business]** so users can see the distinction.
📝 Formatting:
- Use **bold** for names or titles.
- Add a short one-line explanation under each idea.
"""


# ---- Safe response extractor ----
def get_response_text(resp):
    """Safely extract text from Gemini response."""
    try:
        if not resp:
            return None

        if hasattr(resp, "candidates") and resp.candidates:
            for c in resp.candidates:
                if hasattr(c, "content") and c.content and hasattr(c.content, "parts"):
                    parts = c.content.parts
                    if parts and hasattr(parts[0], "text"):
                        return parts[0].text.strip()

        if hasattr(resp, "text") and resp.text:
            return resp.text.strip()
    except Exception:
        return None
    return None

# ---- Main chat function ----
def idea_forge_chat(message, history):
    start_time = time.time()
    conversation = ""

    # Build chat history
    for turn in history:
        user_text = turn[0] if len(turn) > 0 else ""
        bot_text = turn[1] if len(turn) > 1 else ""
        if user_text:
            conversation += f"User: {user_text}\n"
        if bot_text:
            conversation += f"IdeaForge: {bot_text}\n"

    # Build prompt
    prompt = f"{SYSTEM_PROMPT}\n{conversation}\nUser: {message}\nIdeaForge (respond creatively and directly):"

    # Processing notifier (background)
    def delayed_notice():
        time.sleep(5)
        if time.time() - start_time < 10:
            print("⏳ Processing for better answer...")

    threading.Thread(target=delayed_notice, daemon=True).start()
    
    if "service" in message.lower() and "business" not in message.lower():
        message = "Give me creative service ideas only, not full businesses. " + message
    elif "business" in message.lower() and "service" not in message.lower():
        message = "Give me business ideas only — not personal services. " + message

    try:
        # Generate content
        response = model.generate_content(
            prompt, generation_config={"max_output_tokens": 768}
        )
        bot_text = get_response_text(response)

        # Retry once if needed (e.g., finish_reason = 2 or empty)
        if not bot_text or "finish_reason=2" in str(response):
            response = model.generate_content(prompt + "\nTry again creatively and safely:")
            bot_text = get_response_text(response)

        # If still nothing
        if not bot_text:
            bot_text = "⚠️ I couldn’t generate a proper response this time — please try again!"

    except Exception as e:
        if "429" in str(e):
            bot_text = "🚦 Gemini API quota limit reached — please wait a bit or use a new key."
        else:
            bot_text = f"⚠️ Error: {str(e)}"

    # Add delay notice if slow
    elapsed = time.time() - start_time
    if elapsed > 10:
        bot_text = "⏳ Processing took a bit longer for a detailed response...\n\n" + bot_text

    return bot_text


# ---- Modern Dark UI ----
modern_css = """
body {
  background: linear-gradient(180deg, #0b1120 0%, #1a2538 100%);
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color: #f8fafc;
}
.gradio-container {
  background: transparent !important;
  padding: 22px;
}
#component-0 {
  background: #1e293b;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}
h1 {
  color: #e2e8f0;
  font-weight: 700;
  text-align: center;
}
.description {
  color: #cbd5e1;
  text-align: center;
    margin-bottom: 16px;
}
footer { display: none !important; }
.chat-message { 
  border-radius: 12px;
  padding: 10px 14px;
  margin: 6px 0;
  max-width: 78%;
  line-height: 1.45;
}
.user { 
  background: rgba(59,130,246,0.25);
  color: #f1f5f9;
  align-self: flex-end;
}
.bot { 
  background: #334155;
  color: #f8fafc;
  align-self: flex-start;
  border: 1px solid #475569;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
}
/* Hide chatbot title area completely */
#component-0 .svelte-1ipelgc {
  display: none !important;
}
/* Hide any auto-generated chatbot label */
#component-0 .svelte-1ipelgc {
  display: none !important;
}
/* Input area style */
textarea.svelte-1ipelgc, textarea.svelte-1ipelgc:focus {
  background: rgba(30, 41, 59, 0.6) !important;
  color: #f8fafc !important;
  border: 1px solid #475569 !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  font-size: 15px !important;
  box-shadow: 0 0 12px rgba(0,0,0,0.2);
  transition: all 0.2s ease-in-out;
}
textarea.svelte-1ipelgc:focus {
  border-color: #60a5fa !important;
  box-shadow: 0 0 10px rgba(96,165,250,0.4);
}
/* Send button styling */
button.svelte-1ipelgc {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-radius: 50% !important;
  color: white !important;
  width: 40px !important;
  height: 40px !important;
  box-shadow: 0 4px 14px rgba(37,99,235,0.4);
  transition: 0.2s;
}
button.svelte-1ipelgc:hover {
  transform: scale(1.07);
  box-shadow: 0 0 18px rgba(96,165,250,0.6);
}
/* Keep chat bubbles smooth */
.chat-message {
  border-radius: 12px;
  padding: 10px
"""

# ---- Gradio Interface ----
iface = gr.ChatInterface(
    fn=idea_forge_chat,
    title="",  # Removes "Chatbot"
    description="💡 IdeaForge helps you think, write, and create effortlessly.",
    theme="soft",
    css=modern_css,
    examples=[
        ["Brainstorm a catchy name and slogan for a new coffee brand ☕"],
        ["List 3 creative social media post ideas for a clothing brand 👕"],
    ],
)
if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
