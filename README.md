# MacroSnap 🥗

MacroSnap is a friendly AI nutrition buddy built with Streamlit and Google Gemini. 
You can type a description or snap a photo of your meal, and the AI will estimate the calories and macros (protein/carbs/fats). Once you are done logging your meals, you can send a clean, formatted summary directly to your Telegram app.

## Features
- **AI Chat & Vision:** Powered by Google Gemini to analyze text or food images.
- **Seamless Telegram Integration:** Uses Deep Linking (`?start=`) so users can securely connect their Telegram account without typing confusing Chat IDs.
- **Smart Streaming:** The summary is blasted to Telegram using a real-time typing effect (`editMessageText`) for a polished experience that doesn't spam notifications.

## Requirements
- Python 3.9+
- A Google Gemini API Key
- A Telegram Bot Token (from @BotFather)

## How to run locally

1. **Clone the repository and set up a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Secrets**
   - Rename `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Open it and paste your real `GEMINI_API_KEY` and `TELEGRAM_BOT_TOKEN`.
   *(Note: `secrets.toml` is ignored by git so your keys remain safe).*

4. **Run the App**
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501`, enter your name, click the Telegram Link, and start tracking!
