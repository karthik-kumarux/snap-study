# Project Ideas for you to Build

Everyone builds MacroSnap together in the live session. But for your own project, pick one of the ideas below \- or design your own, using the same building blocks: Gemini vision \+ chat, and WhatsApp / Telegram / Email as the action tool.

🤔 Have a doubt? Ask here:

[https://bit.ly/ai-vision-chatbot-doubts](https://bit.ly/ai-vision-chatbot-doubts) 

## Choosing Your Action Tool

All three options plug into the same place in the app: wherever MacroSnap calls send\_whatsapp(...), your version calls send\_email(...) or send\_telegram(...) instead. Everything else \- onboarding, the chat, the prompts \- stays the same.

### Option A · WhatsApp (via Twilio)

* Same as MacroSnap 

* Con: free only at small/sandbox scale, and business-initiated sends need an approved Content Template.

### Option B · Gmail (SMTP) — completely free (Recommended)

* Uses Python's built-in smtplib \- no third-party account or paid plan needed, just the your own Gmail address.

* Setup: on the sending Gmail account, turn on 2-Step Verification, then create an App Password at myaccount.google.com/apppasswords. Use that 16-character App Password in code \- never the real account password.

import smtplib  
from email.mime.text import MIMEText  
   
GMAIL\_ADDRESS \= st.secrets\["GMAIL\_ADDRESS"\]  
GMAIL\_APP\_PASSWORD \= st.secrets\["GMAIL\_APP\_PASSWORD"\]  
   
   
def send\_email(to\_address, subject, body):  
    message \= MIMEText(body)  
    message\["Subject"\] \= subject  
    message\["From"\] \= GMAIL\_ADDRESS  
    message\["To"\] \= to\_address  
   
    with smtplib.SMTP\_SSL("smtp.gmail.com", 465\) as server:  
        server.login(GMAIL\_ADDRESS, GMAIL\_APP\_PASSWORD)  
        server.send\_message(message)

* Onboarding form asks for the recipient's email address instead of a WhatsApp number; everything downstream (the summary prompt, the button) is unchanged.

### Option C · Telegram (bot) — completely free

* No phone-number verification, no sandbox join code \- just a bot token.

* Setup: open Telegram, message @BotFather, send /newbot, and follow the prompts to get a bot token. Then have the recipient send any message to the new bot once \- Telegram needs that before the bot is allowed to message them \- and note their chat\_id (the getUpdates API, or a library helper, reads it back).

import asyncio  
from telegram import Bot  
   
TELEGRAM\_BOT\_TOKEN \= st.secrets\["TELEGRAM\_BOT\_TOKEN"\]  
   
   
def send\_telegram(chat\_id, text):  
    bot \= Bot(token=TELEGRAM\_BOT\_TOKEN)  
    asyncio.run(bot.send\_message(chat\_id=chat\_id, text=text))

* Requires the python-telegram-bot package (already used in the earlier Telegram Lens prototype from this workshop series) \- add it to requirements.txt.

*Whichever tool you pick, keep the same shape: onboard once to collect the destination (number / email / chat\_id), build the summary with Gemini exactly like MacroSnap does, then hand that text to one send function.*

### 1\. Snap & Study  ·  Easy

* You photograph a problem, diagram, or page of notes they don't understand.

* Gemini explains it in plain language and breaks down the key concept.

* A "send to WhatsApp / Telegram / Email" button texts the explanation to the student, so it's saved outside the app.

**What you will learn:**

* Prompting Gemini for clear, structured explanations rather than just descriptions

* Reusing the onboard → chat → WhatsApp / Telegram / Email \- send pattern from MacroSnap for a different use case

### 2\. Receipt & Expense Tracker / Bill Splitter  ·  Easy

* You photograph a receipt or bill.

* Gemini reads the itemized amounts and total, and (optionally) splits it evenly or by item across a number of people.

* The breakdown is sent to WhatsApp / Telegram / Email \- handy as a quick "emergency bill splitter."

**What you will learn:**

* Getting structured data (amounts, totals) out of a photo, not just a description

* Turning a real everyday chore \- splitting a bill \- into a 10-second automation

### 3\. Deadline Tracker  ·  Medium

* You photograph a syllabus, timetable, or assignment sheet.

* Gemini extracts the dates and deadlines it can find.

* A digest of upcoming deadlines is sent to WhatsApp / Telegram / Email as a reminder.

**What you will learn:**

* Extracting dates/structured lists reliably from messy real-world photos

* Designing a prompt that fails gracefully when the photo doesn't contain what's expected

## Your Own Idea

Prefer to build something else? Any idea is fine as long as it follows the same shape as everything above:

1. Pick a photo (or short text) a person would realistically want AI to look at \- a menu, a plant, a whiteboard, a product label, anything.

2. Write a system prompt in prompts.py that keeps Gemini scoped to that one job, the same way MacroSnap's system prompt keeps it on food and fitness.

3. Reuse the onboarding → chat → WhatsApp / Telegram / Email \- send pattern \- swap out what the chat is about, not the structure.

4. Pick one clear "action" for the WhatsApp / Telegram / Email button to trigger \- a summary, a reminder, a list, a recommendation.