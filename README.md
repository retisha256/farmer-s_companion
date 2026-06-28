# 🌾 Farmer's Companion

An AI-powered agricultural assistant for Ugandan smallholder farmers, accessible via **USSD**, **Voice**, and **SMS** — no smartphone or internet required.

---

## The Problem

Uganda has **5.2 million smallholder farmers** who produce 80% of the country's food. Yet:

- 85% of rural farmers own only 2G feature phones
- Most farming knowledge is available only in English
- Farmers speak Luganda, Runyankole, Acholi, and Kiswahili
- Internet access in rural areas is limited or unaffordable

Farmers need weather forecasts, market prices, pest diagnosis, and expert advice — delivered in their own language, on a basic phone.

---

## The Solution

Farmer's Companion delivers agricultural intelligence through channels that work on **any phone**, on **any network**, with **no internet**:

| Channel | How to use | What it does |
|---------|-----------|-------------|
| **USSD** | Dial `*384*400111#` | Keypad menu, instant text responses |
| **Voice** | Call the virtual number | Spoken menus, keypad responses |
| **SMS** | Text keywords | Weather, prices, registration |

All three channels share the same AI backend, translation layer, and farmer profiles.

---

## Features

### 🌍 5-Language Support
- English
- Kiswahili
- Luganda
- Runyankole
- Acholi

Language is selected on first use and remembered across all channels. Every response — menus, weather, market prices, AI advice — is delivered in the farmer's chosen language.

### ☀️ Weather Forecasts
- Current weather for farmer's registered location
- 3-day forecast
- AI-generated farming tip based on current conditions (e.g. "Rain expected — delay fertilizer application")

### 💰 Market Prices
- Live crop prices in UGX (Ugandan Shillings)
- Crops: Maize, Beans, Cassava, Coffee
- Falls back to Uganda baseline prices when live API is unavailable

### 🐛 Pest Diagnosis
- AI-powered diagnosis from symptom selection
- Symptoms: yellow/wilting leaves, holes in leaves, stunted growth
- Returns: likely cause, remedy, prevention tip

### 🌱 Farming Tips
- Planting tips
- Pest & disease alerts
- Harvest advice

### 🤖 Ask AI
- Crop cultivation advice
- Soil preparation tips
- Fertilizer recommendations
- Irrigation guidance
- Powered by Google Gemini (primary) → OpenAI (fallback) → curated static responses

### 👤 Farmer Profile
- Phone number-based registration
- Saves name, location, crops, and language preference
- Register via USSD or by texting `REGISTER <name>`

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Africa's Talking                    │
│          (USSD gateway / Voice / SMS)                │
└───────────────────┬────────────────────────────────┘
                    │ POST (webhooks)
                    ▼
┌─────────────────────────────────────────────────────┐
│                Django Backend                        │
│                                                     │
│  /ussd/callback/   →  USSD handler                  │
│  /voice/callback/  →  Voice session handler         │
│  /sms/callback/    →  SMS keyword handler           │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Translation │  │ AI Assistant │  │  Weather  │  │
│  │  Service    │  │  (Gemini /   │  │    API    │  │
│  │  (5 langs)  │  │   OpenAI /   │  │  (OWM)   │  │
│  │             │  │   Static)    │  │           │  │
│  └─────────────┘  └──────────────┘  └───────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │              SQLite / PostgreSQL             │   │
│  │  Farmer profiles · Language prefs · Sessions │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### App Structure

```
farmer_companion/
├── farmers_companion/       # Django project settings
├── apps/
│   ├── core/                # Shared base model, AT service
│   ├── ussd/                # USSD handler, menus, translation, AI
│   │   └── services/
│   │       ├── ussd_handler.py      # Session routing
│   │       ├── menu_structure.py    # Menu builders (all languages)
│   │       ├── translations.py      # 5-language translation engine
│   │       └── ai_assistant.py      # Gemini → OpenAI → static fallback
│   ├── voice/               # Voice call handler
│   │   └── services/
│   │       ├── voice_session.py     # Per-hop state machine
│   │       └── voice_menu.py        # AT ActionScript XML builders
│   ├── sms/                 # SMS keyword handler
│   ├── weather/             # OpenWeatherMap integration
│   ├── farmers/             # Farmer profiles
│   ├── payments/            # (Future: Airtime/M-Pesa)
│   └── analytics/           # Usage tracking
├── templates/               # HTML templates
├── static/                  # CSS, JS
├── docs/                    # API and deployment docs
└── scripts/                 # Seed data, test scripts
```

---

## USSD Flow

```
Dial *384*400111#
       │
       ▼
Choose language:
  1. English  2. Kiswahili  3. Luganda  4. Runyankole  5. Acholi
       │
       ▼
Main Menu (in chosen language):
  1. Weather Forecast
  2. Market Prices
  3. Pest Diagnosis
  4. Farming Tips
  5. Ask AI
  6. My Profile
  7. Change Language
  0. Exit
```

Returning users skip language selection — their preference is saved to the database.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django 4.2 |
| API Framework | Django REST Framework |
| Gateway | Africa's Talking (USSD, Voice, SMS) |
| AI (primary) | Google Gemini 2.0 Flash |
| AI (fallback) | OpenAI GPT-3.5 Turbo |
| AI (offline) | Curated static responses |
| Weather | OpenWeatherMap API |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Translation | Built-in dict + AI fallback |
| Server | Gunicorn + WhiteNoise |
| Tunnel (dev) | ngrok |

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- ngrok ([download](https://ngrok.com/download))

### 1. Clone and install

```bash
git clone https://github.com/retisha256/farmer-s_companion.git
cd farmer_companion

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure environment

Copy the template and fill in your keys:

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/Mac
```

Required values in `.env`:

```env
SECRET_KEY=your-django-secret-key        # generate at https://djecrety.ir
AT_USERNAME=sandbox
AT_API_KEY=your-key-from-africastalking
WEATHER_API_KEY=your-openweathermap-key  # free at openweathermap.org
GEMINI_API_KEY=your-gemini-key           # free at aistudio.google.com
OPENAI_API_KEY=your-openai-key           # optional, Gemini is primary
```

### 3. Set up the database

```bash
python manage.py migrate
python manage.py createsuperuser         # optional, for /admin
python scripts/seed_data.py              # optional mock data
```

### 4. Run

**Terminal 1 — Django:**
```bash
python manage.py runserver
```

**Terminal 2 — ngrok tunnel:**
```bash
ngrok http 8000
```

Copy the `https://` URL from ngrok (e.g. `https://abc123.ngrok-free.app`).

### 5. Configure Africa's Talking dashboard

Log in at [account.africastalking.com](https://account.africastalking.com) and set:

| Product | Callback URL |
|---------|-------------|
| USSD | `https://your-ngrok-url/ussd/callback/` |
| Voice | `https://your-ngrok-url/voice/callback/` |
| SMS | `https://your-ngrok-url/sms/callback/` |

Also add your ngrok domain to `.env`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,your-ngrok-domain.ngrok-free.app
```
Then restart the Django server.

### 6. Test

In the Africa's Talking simulator, dial your USSD shortcode. You should see:

```
Welcome to Farmer's Companion
Choose language:
1. English
2. Kiswahili
3. Luganda
4. Runyankole
5. Acholi
```

---

## SMS Commands

| Command | Description |
|---------|-------------|
| `WEATHER <location>` | Current weather for a location |
| `PRICE <crop>` | Market price for a crop |
| `REGISTER <name>` | Register your farmer profile |
| `HELP` | List all available commands |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ussd/callback/` | POST | Africa's Talking USSD webhook |
| `/voice/callback/` | POST | Africa's Talking Voice webhook |
| `/sms/callback/` | POST | Africa's Talking SMS webhook |
| `/api/weather/current/?location=<city>` | GET | Current weather |
| `/api/farmers/register/` | POST | Register a farmer |
| `/api/analytics/summary/` | GET | Usage statistics |
| `/admin/` | GET | Django admin panel |

Full API documentation: [`docs/api.md`](docs/api.md)

---

## AI Resilience

The AI advisory feature uses a three-tier fallback to ensure farmers always get a useful response, even when API quotas are exhausted:

```
Request
   │
   ▼
1. Google Gemini 2.0 Flash  ← primary (higher free quota)
   │ (if quota exhausted)
   ▼
2. OpenAI GPT-3.5 Turbo     ← secondary fallback
   │ (if quota exhausted)
   ▼
3. Curated static responses  ← always available, instant, zero cost
```

When quota is exhausted, the system detects it on the first failure and routes all subsequent requests directly to static responses — keeping response time well under Africa's Talking's 5-second USSD timeout.

---

## Translation Architecture

All responses go through the translation pipeline:

```
English text
     │
     ▼
1. Cache check (24h TTL)         ← instant
     │ (cache miss)
     ▼
2. Built-in dictionary lookup    ← instant, covers all menu strings,
     │ (not found)                  weather labels, tips, AI responses
     ▼
3. OpenAI translation API        ← for novel dynamic text
     │ (quota exhausted)
     ▼
4. English fallback              ← always safe
```

The built-in dictionary covers all static menus, farming tips, AI static fallbacks, weather condition strings, and common response phrases — so translation works at full speed even when both AI APIs are quota-exhausted.

---

## Running Tests

```bash
python manage.py test apps.ussd
```

Current test coverage: **69 tests** across translation service, language selection, USSD routing, weather, market prices, pest diagnosis, farming tips, Ask AI, and HTTP view layer.

---

## Deployment

See [`docs/deployment.md`](docs/deployment.md) for production deployment with Gunicorn + Nginx + PostgreSQL.

Key checklist:
- Set `DEBUG=False`
- Use a strong `SECRET_KEY`
- Switch to PostgreSQL
- Run `python manage.py collectstatic`
- Set `ALLOWED_HOSTS` to your production domain

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Built for Uganda 🇺🇬

*Farmer's Companion is built for the 5.2 million smallholder farmers who feed Uganda — accessible on any phone, in any language, anywhere.*
