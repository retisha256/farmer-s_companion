# Setup Guide

## Prerequisites
- Python 3.10+
- pip
- Redis (for Celery — optional during development)

## Installation

```bash
# Clone the repo
git clone https://github.com/retisha256/farmer-s_companion.git
cd farmer_companion

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit .env and fill in your API keys (see .env for all required values)

# Create and apply database migrations
python manage.py makemigrations core voice sms ussd weather farmers payments analytics
python manage.py migrate

# Create a Django superuser (for /admin)
python manage.py createsuperuser

# Seed mock data (optional)
python scripts/seed_data.py

# Start the development server
python manage.py runserver
```

## Exposing Your Local Server with ngrok

Africa's Talking needs a public URL to send webhooks to your machine.
ngrok creates a secure tunnel from the internet to your local server.

### One-time setup

1. Download ngrok from https://ngrok.com/download (Windows ZIP, extract ngrok.exe)
2. Sign up for a free account at https://dashboard.ngrok.com
3. Copy your authtoken from the dashboard and run:
   ```
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

### Every development session

**Terminal 1 — Django server:**
```bash
venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 — ngrok tunnel:**
```bash
ngrok http 8000
```

ngrok will display a public URL like:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:8000
```

### After getting your ngrok URL

1. Add it to ALLOWED_HOSTS in your .env:
   ```
   ALLOWED_HOSTS=localhost,127.0.0.1,abc123.ngrok-free.app
   ```

2. Restart the Django server.

3. Set these callback URLs in your Africa's Talking dashboard:
   - SMS callback:   https://abc123.ngrok-free.app/sms/callback/
   - USSD callback:  https://abc123.ngrok-free.app/ussd/callback/
   - Voice callback: https://abc123.ngrok-free.app/voice/callback/

> Note: The free ngrok URL changes every time you restart ngrok.
> Update the AT dashboard each new session, or upgrade to a paid plan for a fixed domain.

## Africa's Talking Credentials

Get these from https://account.africastalking.com:

| Variable      | Where to find it                          |
|---------------|-------------------------------------------|
| AT_USERNAME   | Use "sandbox" while testing               |
| AT_API_KEY    | Settings → API Key                        |
| AT_SENDER_ID  | SMS → Sender IDs (leave blank in sandbox) |
| AT_SHORTCODE  | USSD → your assigned shortcode            |

## Other API Keys

| Variable          | Where to get it                              |
|-------------------|----------------------------------------------|
| SECRET_KEY        | Generate at https://djecrety.ir              |
| WEATHER_API_KEY   | Register at https://openweathermap.org/api   |
| OPENAI_API_KEY    | https://platform.openai.com/api-keys         |
| GEMINI_API_KEY    | https://aistudio.google.com/app/apikey       |
