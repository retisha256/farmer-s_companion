# Setup Guide

## Prerequisites
- Python 3.10+
- pip
- Redis (for Celery)

## Installation

```bash
# Clone the repo
git clone https://github.com/gilianfavour/Farmer-s-Companion.git
cd farmer_companion

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env
# Edit .env with your API keys

# Run migrations
python manage.py migrate

# Seed mock data (optional)
python scripts/seed_data.py

# Start the development server
python manage.py runserver
```
