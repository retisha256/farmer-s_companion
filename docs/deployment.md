# Deployment Guide

## Production Checklist
- Set `DEBUG=False` in `.env`
- Set a strong `SECRET_KEY`
- Configure `ALLOWED_HOSTS` with your domain
- Use PostgreSQL instead of SQLite
- Run `python manage.py collectstatic`
- Use Gunicorn as the WSGI server
- Set up Nginx as a reverse proxy
- Configure SSL/TLS certificate

## Gunicorn

```bash
gunicorn farmers_companion.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Environment Variables
See `.env` for all required variables.
