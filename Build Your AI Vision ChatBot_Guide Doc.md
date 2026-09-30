# Step-by-Step Build Guide — MacroSnap

MacroSnap is the flagship project built live in this workshop: a Streamlit chat app where a student enters their name and WhatsApp number once, then chats with an AI nutrition buddy \- typing a question or attaching a photo of a meal \- and gets an instant calorie/macro estimate. One button sends a full summary of the conversation straight to WhatsApp. It's built with Gemini (chat \+ vision) and Twilio (WhatsApp) \- no OpenCV, no MediaPipe, no model training.

🤔 Have a doubt? Ask here:

[https://bit.ly/ai-vision-chatbot-doubts](https://bit.ly/ai-vision-chatbot-doubts) 

## What you'll need before building the project

* Python 3.9 or newer installed

* Basic comfort with Python (this is the one prerequisite for students)

* A free Google AI Studio account, for a Gemini API key

* A free Twilio account, for the WhatsApp sandbox

## Project structure

macrosnap/  
├── app.py                        \# the app itself  
├── prompts.py                    \# the AI's personality, kept separate  
├── requirements.txt              \# dependencies  
├── .gitignore                    \# keeps secrets.toml out of GitHub  
└── .streamlit/  
    └── secrets.toml.example      \# template \- copy to secrets.toml and fill in

## Step 1 — Environment & keys

1. Create a project folder, e.g. macrosnap/

2. Create a virtual environment: python \-m venv venv

3. Activate it \- macOS/Linux: source venv/bin/activate · Windows PowerShell: .\\\\venv\\\\Scripts\\\\Activate.ps1 (run Set-ExecutionPolicy \-Scope Process \-ExecutionPolicy Bypass first if blocked) · Windows cmd.exe: venv\\\\Scripts\\\\activate.bat

4. Install dependencies: pip install \-r requirements.txt

5. Get a Gemini API key from Google AI Studio (aistudio.google.com → Get API key)

6. Sign up free at twilio.com/try-twilio, then from the Console copy your Account SID and Auth Token

7. Under Messaging → Try it out → Send a WhatsApp message, find your sandbox number and join code (e.g. "join happy-tiger")

8. From the WhatsApp number you'll test with, send that join message to the sandbox number \- this opt-in is required and expires after \~72 hours of inactivity

9. In the Twilio Console, go to Messaging → Content Template Builder and create a Text template with one variable for the recipient's name and one for the summary (e.g. "Hi {{1}}, here's your MacroSnap summary:\\n\\n{{2}}") \- note its Content SID (starts with HX...)

*Why a Content Template? WhatsApp's business-messaging policy only allows free-form text replies within a 24-hour window opened by the customer. A message your app sends on its own initiative \- like our WhatsApp summary button \- counts as business-initiated, so Twilio requires an approved template rather than arbitrary text.*

## 

## Step 2 — requirements.txt

streamlit  
google-genai  
twilio

## Step 3 — prompts.py: giving MacroSnap a personality

Keeping prompts in their own file separates the AI's "personality" from the app's logic, so either can be tweaked independently.

SYSTEM\_PROMPT \= """You are MacroSnap, a friendly AI nutrition buddy.  
Your ONLY job is to help the user understand what they're eating \-  
estimating calories and macros from a photo or a text description.  
   
If the user asks about anything unrelated to food, nutrition, meals, or  
fitness, politely decline and steer the conversation back to food.  
   
When estimating a meal from a photo or description, always include:  
1\. What the meal appears to be  
2\. Estimated calories  
3\. Estimated protein / carbs / fat (rough is fine \- say so)  
   
Keep replies short, friendly, and conversational \- no markdown formatting."""  
   
   
WELCOME\_MESSAGE\_TEMPLATE \= (  
    "Hey {name}\! I'm MacroSnap 🥗 \- your instant calorie & macro decoder.\\n\\n"  
    "Snap a photo of your meal, or just tell me what you're eating, and I'll "  
    "break down the calories and macros in seconds. No food diary, no "  
    "guesswork.\\n\\n"  
    "When you're done, hit \\"Send details to WhatsApp\\" below and I'll text "  
    "your full summary straight to your phone."  
)  
   
   
SUMMARY\_REQUEST\_PROMPT \= (  
    "Summarize every meal we've discussed in this conversation into one "  
    "WhatsApp-friendly message: list each item with its estimated calories, "  
    "then give a running total of calories and macros (protein/carbs/fat) "  
    "for everything combined. Keep it short, plain text with a couple of "  
    "emojis, no markdown \- ready to send exactly as you write it."  
)

* SYSTEM\_PROMPT \- sets the persona and, critically, the instruction that keeps replies on-topic (food/fitness only). This is set once per conversation via Gemini's system\_instruction, so it applies to every message without any extra if-statements in app.py.

* WELCOME\_MESSAGE\_TEMPLATE \- the first message a student sees; {name} gets filled in after onboarding.

* SUMMARY\_REQUEST\_PROMPT \- not shown to the user. It's sent to Gemini behind the scenes when the WhatsApp button is clicked, asking it to reread the whole conversation and produce one clean summary.

## 

## 

## 

## Step 4 — Connecting to Gemini

Build the Gemini client once, cached, so it survives every Streamlit rerun:

@st.cache\_resource  
def get\_gemini\_client():  
    return genai.Client(api\_key=GEMINI\_API\_KEY)  
   
   
gemini\_client \= get\_gemini\_client()

*Gotcha to flag live: Streamlit re-executes the entire script top to bottom on every interaction. If genai.Client(...) is created as a plain top-level variable, a brand-new client is built on every rerun and the previous one is garbage-collected \- closing its connection. Any chat session created from that old client then fails with "Cannot send a request, as the client has been closed." Wrapping creation in @st.cache\_resource builds the client once per session and reuses it, so every chat and every message shares the same live connection.*

## Step 5 — Building the onboarding screen

if "onboarded" not in st.session\_state:  
    st.title("🥗 MacroSnap")  
    st.caption("Snap it. Track it. Text yourself the results.")  
    with st.form("onboarding\_form"):  
        name \= st.text\_input("Your name")  
        whatsapp\_number \= st.text\_input(  
            "WhatsApp number (with country code)",  
            placeholder="+91XXXXXXXXXX",  
        )  
        submitted \= st.form\_submit\_button("Let's go 🚀")  
    if submitted:  
        if not name.strip() or not whatsapp\_number.strip():  
            st.warning("Please fill in both your name and WhatsApp number.")  
        else:  
            st.session\_state.name \= name.strip()  
            st.session\_state.whatsapp\_number \= whatsapp\_number.strip()  
            st.session\_state.chat \= gemini\_client.chats.create(  
                model=MODEL\_NAME,  
                config=types.GenerateContentConfig(system\_instruction=SYSTEM\_PROMPT),  
            )  
            st.session\_state.messages \= \[\]  
            st.session\_state.onboarded \= True  
            st.rerun()  
    st.stop()

* if "onboarded" not in st.session\_state is the standard Streamlit pattern for "show this only once per session".

* Submitting the form is where the actual Gemini chat session is born \- gemini\_client.chats.create(...) with system\_instruction=SYSTEM\_PROMPT gives the conversation its memory and its personality, and it's stored in session state so every later message reuses the same conversation.

* st.rerun() forces Streamlit to immediately restart the script so it picks up onboarded \= True and skips straight past the form next time.

## Step 6 — Building the chat interface

def render\_message(message):  
    with st.chat\_message(message\["role"\]):  
        if message\["kind"\] \== "text":  
            st.write(message\["content"\])  
        elif message\["kind"\] \== "image":  
            st.image(message\["content"\])  
   
   
def add\_message(role, kind, content):  
    st.session\_state.messages.append({"role": role, "kind": kind, "content": content})  
    render\_message(st.session\_state.messages\[-1\])  
   
   
\# ...  
   
if not st.session\_state.messages:  
    add\_message("assistant", "text", WELCOME\_MESSAGE\_TEMPLATE.format(name=st.session\_state.name))  
else:  
    for message in st.session\_state.messages:  
        render\_message(message)

* Every message is stored as a small dict with a role (user/assistant), a kind (text/image) and the content \- one render\_message function handles both a typed question and an uploaded photo the same way.

* add\_message does two things at once: saves the message to history and draws it on screen immediately.

* The welcome message only fires the very first time the chat is empty; after that, history is replayed from session state on every rerun.

## Step 7 — Handling input: text and photos

def ask\_gemini(parts):  
    try:  
        return st.session\_state.chat.send\_message(parts).text  
    except Exception as error:  
        return f"Sorry, something went wrong: {error}"  
   
   
user\_input \= st.chat\_input(  
    "Ask a question, or attach a photo of your meal",  
    accept\_file=True,  
    file\_type=\["jpg", "jpeg", "png"\],  
)  
   
if user\_input:  
    photo \= user\_input.files\[0\] if user\_input.files else None  
    text \= user\_input.text  
    parts \= \[\]  
   
    if photo is not None:  
        photo\_bytes \= photo.getvalue()  
        add\_message("user", "image", photo\_bytes)  
        parts.append(types.Part.from\_bytes(data=photo\_bytes, mime\_type=photo.type))  
    if text:  
        add\_message("user", "text", text)  
        parts.append(text)  
    elif photo is not None:  
        parts.append("What is this meal? Give me the calories and macros.")  
   
    with st.spinner("Crunching the numbers..."):  
        answer \= ask\_gemini(parts)  
    add\_message("assistant", "text", answer)

* st.chat\_input(accept\_file=True, ...) is one input box that takes either typed text or an attached photo \- the Google-Lens-style feel comes from here.

* types.Part.from\_bytes(...) is the actual vision step: it hands the raw image bytes and mime type to Gemini.

* If a photo is attached with no caption, the code quietly supplies its own instruction, so a bare photo still works.

* Because ask\_gemini always calls the same st.session\_state.chat, every message stacks onto one conversation \- a follow-up question like "how much protein was in that?" just works.

## Step 8 — Sending the summary to WhatsApp

def clean\_whatsapp\_text(text):  
    if not text:  
        return "No nutrition summary available."  
    text \= " ".join(text.split())  
    return text\[:1500\] \+ "..." if len(text) \> 1500 else text  
   
   
def send\_whatsapp(to\_number, user\_name, summary):  
    \# Content template expects {{1}} \= name, {{2}} \= summary.  
    try:  
        content\_variables \= json.dumps(  
            {"1": user\_name, "2": clean\_whatsapp\_text(summary)}, ensure\_ascii=False  
        )  
        message \= twilio\_client.messages.create(  
            from\_=TWILIO\_WHATSAPP\_FROM,  
            to=f"whatsapp:{to\_number}",  
            content\_sid=TWILIO\_CONTENT\_SID,  
            content\_variables=content\_variables,  
        )  
        return True, message.sid  
    except Exception as error:  
        return False, str(error)  
   
   
header\_col, button\_col \= st.columns(\[5, 2\], vertical\_alignment="center")  
   
with header\_col:  
    st.title("🥗 MacroSnap")  
   
with button\_col:  
    send\_disabled \= len(st.session\_state.messages) \<= 2  
    if st.button("📤 Send to WhatsApp", disabled=send\_disabled, use\_container\_width=True):  
        with st.spinner("Summarizing your day..."):  
            summary \= ask\_gemini(\[SUMMARY\_REQUEST\_PROMPT\])  
        success, info \= send\_whatsapp(st.session\_state.whatsapp\_number, st.session\_state.name, summary)  
        if success:  
            st.success("Sent\! Check your WhatsApp 📲")  
        else:  
            st.error(f"Couldn't send that: {info}")

* The button sits beside the title, in a st.columns(\[5, 2\], vertical\_alignment="center") layout.

* send\_disabled \= len(st.session\_state.messages) \<= 2 keeps the button greyed out until there's an actual logged exchange (not just the welcome message) \- a disabled button can't be clicked, so there's no need for a separate "log a meal first" warning.

* The click handler reuses ask\_gemini, but this time sends the hidden SUMMARY\_REQUEST\_PROMPT \- Gemini rereads everything said in the conversation and writes one clean recap.

* send\_whatsapp sends via Twilio's Content API (content\_sid \+ content\_variables) instead of a plain body string, because WhatsApp requires an approved template for this kind of business-initiated message (see Step 1's note).

## Full app.py (reference)

The complete file, top to bottom, exactly as it should look after all eight steps above:

import json  
   
import streamlit as st  
from google import genai  
from google.genai import types  
from twilio.rest import Client as TwilioClient  
   
from prompts import SUMMARY\_REQUEST\_PROMPT, SYSTEM\_PROMPT, WELCOME\_MESSAGE\_TEMPLATE  
   
MODEL\_NAME \= "gemini-3.5-flash"  
st.set\_page\_config(page\_title="MacroSnap", page\_icon="🥗")  
   
GEMINI\_API\_KEY \= st.secrets\["GEMINI\_API\_KEY"\]  
TWILIO\_ACCOUNT\_SID \= st.secrets\["TWILIO\_ACCOUNT\_SID"\]  
TWILIO\_AUTH\_TOKEN \= st.secrets\["TWILIO\_AUTH\_TOKEN"\]  
TWILIO\_WHATSAPP\_FROM \= st.secrets\["TWILIO\_WHATSAPP\_FROM"\]  
TWILIO\_CONTENT\_SID \= st.secrets\["TWILIO\_CONTENT\_SID"\]  
   
   
@st.cache\_resource  
def get\_gemini\_client():  
    return genai.Client(api\_key=GEMINI\_API\_KEY)  
   
   
@st.cache\_resource  
def get\_twilio\_client():  
    return TwilioClient(TWILIO\_ACCOUNT\_SID, TWILIO\_AUTH\_TOKEN)  
   
   
gemini\_client \= get\_gemini\_client()  
twilio\_client \= get\_twilio\_client()  
   
   
def render\_message(message):  
    with st.chat\_message(message\["role"\]):  
        if message\["kind"\] \== "text":  
            st.write(message\["content"\])  
        elif message\["kind"\] \== "image":  
            st.image(message\["content"\])  
   
   
def add\_message(role, kind, content):  
    st.session\_state.messages.append({"role": role, "kind": kind, "content": content})  
    render\_message(st.session\_state.messages\[-1\])  
   
   
def ask\_gemini(parts):  
    try:  
        return st.session\_state.chat.send\_message(parts).text  
    except Exception as error:  
        return f"Sorry, something went wrong: {error}"  
   
   
def clean\_whatsapp\_text(text):  
    if not text:  
        return "No nutrition summary available."  
    text \= " ".join(text.split())  \# collapse whitespace/newlines  
    return text\[:1500\] \+ "..." if len(text) \> 1500 else text  
   
   
def send\_whatsapp(to\_number, user\_name, summary):  
    \# Content template expects {{1}} \= name, {{2}} \= summary.  
    try:  
        content\_variables \= json.dumps(  
            {"1": user\_name, "2": clean\_whatsapp\_text(summary)}, ensure\_ascii=False  
        )  
        message \= twilio\_client.messages.create(  
            from\_=TWILIO\_WHATSAPP\_FROM,  
            to=f"whatsapp:{to\_number}",  
            content\_sid=TWILIO\_CONTENT\_SID,  
            content\_variables=content\_variables,  
        )  
        return True, message.sid  
    except Exception as error:  
        return False, str(error)  
   
   
\# Step 1: onboarding  
if "onboarded" not in st.session\_state:  
    st.title("🥗 MacroSnap")  
    st.caption("Snap it. Track it. Text yourself the results.")  
    with st.form("onboarding\_form"):  
        name \= st.text\_input("Your name")  
        whatsapp\_number \= st.text\_input(  
            "WhatsApp number (with country code)",  
            placeholder="+91XXXXXXXXXX",  
            help="This is the number MacroSnap will text your summary to.",  
        )  
        submitted \= st.form\_submit\_button("Let's go 🚀")  
    if submitted:  
        if not name.strip() or not whatsapp\_number.strip():  
            st.warning("Please fill in both your name and WhatsApp number.")  
        else:  
            st.session\_state.name \= name.strip()  
            st.session\_state.whatsapp\_number \= whatsapp\_number.strip()  
            st.session\_state.chat \= gemini\_client.chats.create(  
                model=MODEL\_NAME,  
                config=types.GenerateContentConfig(system\_instruction=SYSTEM\_PROMPT),  
            )  
            st.session\_state.messages \= \[\]  
            st.session\_state.onboarded \= True  
            st.rerun()  
    st.stop()  
   
\# Step 2: chat interface  
header\_col, button\_col \= st.columns(\[5, 2\], vertical\_alignment="center")  
   
with header\_col:  
    st.title("🥗 MacroSnap")  
   
with button\_col:  
    send\_disabled \= len(st.session\_state.messages) \<= 2  
    if st.button("📤 Send to WhatsApp", disabled=send\_disabled, use\_container\_width=True):  
        with st.spinner("Summarizing your day..."):  
            summary \= ask\_gemini(\[SUMMARY\_REQUEST\_PROMPT\])  
        success, info \= send\_whatsapp(st.session\_state.whatsapp\_number, st.session\_state.name, summary)  
        if success:  
            st.success("Sent\! Check your WhatsApp 📲")  
        else:  
            st.error(f"Couldn't send that: {info}")  
   
st.caption(f"Logged in as {st.session\_state.name} \- updates go to {st.session\_state.whatsapp\_number}")  
   
if not st.session\_state.messages:  
    add\_message("assistant", "text", WELCOME\_MESSAGE\_TEMPLATE.format(name=st.session\_state.name))  
else:  
    for message in st.session\_state.messages:  
        render\_message(message)  
   
user\_input \= st.chat\_input(  
    "Ask a question, or attach a photo of your meal",  
    accept\_file=True,  
    file\_type=\["jpg", "jpeg", "png"\],  
)  
   
if user\_input:  
    photo \= user\_input.files\[0\] if user\_input.files else None  
    text \= user\_input.text  
    parts \= \[\]  
   
    if photo is not None:  
        photo\_bytes \= photo.getvalue()  
        add\_message("user", "image", photo\_bytes)  
        parts.append(types.Part.from\_bytes(data=photo\_bytes, mime\_type=photo.type))  
    if text:  
        add\_message("user", "text", text)  
        parts.append(text)  
    elif photo is not None:  
        parts.append("What is this meal? Give me the calories and macros.")  
   
    with st.spinner("Crunching the numbers..."):  
        answer \= ask\_gemini(parts)  
    add\_message("assistant", "text", answer)

## .streamlit/secrets.toml.example

Copy this to .streamlit/secrets.toml (drop the .example) and fill in real values. Never commit the real secrets.toml \- only this template file.

GEMINI\_API\_KEY \= "your-gemini-api-key-here"  
   
\# From your Twilio Console (console.twilio.com):  
TWILIO\_ACCOUNT\_SID \= "your-twilio-account-sid-here"  
TWILIO\_AUTH\_TOKEN \= "your-twilio-auth-token-here"  
   
\# The Twilio Sandbox's shared WhatsApp number \- leave as-is unless you have  
\# your own approved WhatsApp sender.  
TWILIO\_WHATSAPP\_FROM \= "whatsapp:+14155238886"  
   
\# The Content SID of your WhatsApp Content Template (Twilio Console \>  
\# Messaging \> Content Template Builder). Required because WhatsApp does not  
\# allow plain free-text messages for business-initiated sends.  
TWILIO\_CONTENT\_SID \= "your-content-template-sid-here"

## Running it locally

streamlit run app.py

This opens the app at http://localhost:8501. Onboard with the WhatsApp number that joined your sandbox, try a text question, try a photo, then click the WhatsApp button once you've logged something.

## Deploying — Streamlit Community Cloud

1. Push the project to a GitHub repo. Do not commit .streamlit/secrets.toml \- only secrets.toml.example should be tracked.

2. Go to share.streamlit.io and sign in with GitHub.

3. Click "New app", pick the repo, branch, and app.py as the entry point.

4. In the app's Settings → Secrets panel, paste the same content your local secrets.toml has.

5. Deploy \- you get a public URL, no separate server to manage.

