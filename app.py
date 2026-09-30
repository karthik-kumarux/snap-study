import json
import time
import requests
import uuid

import streamlit as st
from google import genai
from google.genai import types

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.5-flash"
st.set_page_config(page_title="MacroSnap", page_icon="🥗")

# Retrieve keys gracefully since user mentioned they don't have them yet.
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    GEMINI_API_KEY = "dummy_gemini_key"

try:
    TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
except (FileNotFoundError, KeyError):
    TELEGRAM_BOT_TOKEN = "dummy_telegram_token"

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

gemini_client = get_gemini_client()

@st.cache_data(ttl=3600)
def get_telegram_bot_username(token):
    if token == "dummy_telegram_token":
        return "MockMacroSnapBot" # Dummy fallback
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        res_json = response.json()
        if res_json.get("ok"):
            return res_json["result"]["username"]
    except Exception:
        pass
    return "YourBotUsername"

def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])

def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])

def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong (Did you add your Gemini API Key in .streamlit/secrets.toml?):\n{error}"

def send_telegram_chunked(chat_id, summary):
    """
    Sends the summary to Telegram by editing a SINGLE message,
    giving a fast 'typing cursor' streaming effect without spamming notifications!
    """
    if not summary:
        return False, "No nutrition summary available."

    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    # Send a "typing..." status indicator to the top of their Telegram screen
    if TELEGRAM_BOT_TOKEN != "dummy_telegram_token":
        requests.post(f"{base_url}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})

    # Chop into faster, chunkier pieces (15 words at a time)
    words = summary.split()
    chunks = [" ".join(words[i:i+15]) for i in range(0, len(words), 15)]

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Send the very first placeholder message
    first_payload = {"chat_id": chat_id, "text": "📝 *Crunching your summary...*", "parse_mode": "Markdown"}
    message_id = None

    if TELEGRAM_BOT_TOKEN != "dummy_telegram_token":
        try:
            init_msg = requests.post(f"{base_url}/sendMessage", json=first_payload).json()
            if init_msg.get("ok"):
                message_id = init_msg["result"]["message_id"]
        except Exception as e:
            return False, str(e)

    current_text = ""
    for idx, chunk in enumerate(chunks):
        current_text += chunk + " "

        # Add a ✍️ cursor while it's still typing, remove it at the end
        display_text = current_text + (" ✍️" if idx < len(chunks) - 1 else "")
        status_text.write(f"Streaming text...")

        if TELEGRAM_BOT_TOKEN != "dummy_telegram_token" and message_id:
            try:
                # EDIT the exact same message instead of sending an annoying new one
                requests.post(f"{base_url}/editMessageText", json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": display_text
                })
            except Exception:
                pass

        # Wait just 1 second (Telegram limits edits to ~1 per second safely)
        time.sleep(1)
        progress_bar.progress((idx + 1) / len(chunks))

    status_text.empty()
    progress_bar.empty()
    return True, "Summary streamed instantly!"

# Step 1: onboarding
if "onboarded" not in st.session_state:
    st.title("🥗 MacroSnap")
    st.caption("Snap it. Track it. Text yourself the results on Telegram.")

    # 1. Ask for their Name first
    name = st.text_input("Your Name")

    # 2. Generate a unique code so we can find them in the Telegram message logs
    if "sync_code" not in st.session_state:
        st.session_state.sync_code = uuid.uuid4().hex[:8]

    if name.strip():
        st.divider()
        st.write("### Link Your Telegram automatically!")

        if TELEGRAM_BOT_TOKEN == "dummy_telegram_token":
            st.info("You are currently using Mock Mode (no keys yet). Click below to bypass connection.")
            if st.button("Simulate Telegram Link 🚀", type="primary"):
                st.session_state.name = name.strip()
                st.session_state.telegram_chat_id = "123456789_mock_id"
                st.session_state.chat = None
                st.session_state.messages = []
                st.session_state.onboarded = True
                st.rerun()
        else:
            # We have a real token - give them the Deep Link!
            bot_username = get_telegram_bot_username(TELEGRAM_BOT_TOKEN)
            deep_link = f"https://t.me/{bot_username}?start={st.session_state.sync_code}"

            st.write("To safely send you messages, Telegram requires you to start the chat.")
            st.markdown(f"**Step 1:** [Click here to open our Bot securely!]({deep_link})")
            st.markdown(f"**Step 2:** Press the **Start** button in your Telegram app.")

            if st.button("I've clicked Start in Telegram! 🚀", type="primary"):
                with st.spinner("Searching for your connection request..."):
                    connected_chat_id = None
                    try:
                        # Streamlit checks the Telegram getUpdates endpoint to find the sync code
                        res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates")
                        if res.status_code == 200:
                            updates = res.json().get("result", [])
                            # Search the recent messages for the unique sync code
                            for update in updates:
                                message_text = update.get("message", {}).get("text", "")
                                if st.session_state.sync_code in message_text:
                                    connected_chat_id = update["message"]["chat"]["id"]
                                    break
                    except Exception as e:
                        st.error(f"Error checking Telegram: {e}")

                    if connected_chat_id:
                        st.session_state.name = name.strip()
                        st.session_state.telegram_chat_id = str(connected_chat_id)

                        try:
                            st.session_state.chat = gemini_client.chats.create(
                                model=MODEL_NAME,
                                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                            )
                        except Exception:
                            st.session_state.chat = None

                        st.session_state.messages = []
                        st.session_state.onboarded = True
                        st.success("Successfully linked! Loading your chat...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("We couldn't find your message yet. Did you press Start? Wait 2 seconds and try again!")

    st.stop()

# Step 2: chat interface
header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🥗 MacroSnap")

with button_col:
    send_disabled = len(st.session_state.messages) <= 2
    if st.button("📤 Send to Telegram", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your day..."):
            if st.session_state.chat is not None:
                summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            else:
                summary = "This is a mock summary because Gemini is not configured yet."

        success, info = send_telegram_chunked(st.session_state.telegram_chat_id, summary)

        if success:
            st.success("Sent! Check your Telegram 📲")
        else:
            st.error(f"Couldn't send that: {info}")

st.caption(f"Logged in as {st.session_state.name} - updates go to Chat ID: {st.session_state.telegram_chat_id}")

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Ask a question, or attach a photo of your meal",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Give me the calories and macros.")

    with st.spinner("Crunching the numbers..."):
        if st.session_state.chat is not None:
            answer = ask_gemini(parts)
        else:
            answer = "I'm pretending to analyze your meal! (Connect Gemini API Key in .streamlit/secrets.toml to see real AI responses)."
    add_message("assistant", "text", answer)
