"""OpenAI / Gemini integration for voice responses."""
import openai
from django.conf import settings
import logging

logger = logging.getLogger('apps.voice')

openai.api_key = settings.OPENAI_API_KEY


def get_ai_response(prompt: str, model: str = 'gpt-3.5-turbo') -> str:
    """Get a text response from OpenAI for a given farmer query."""
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a helpful agricultural assistant for African farmers. '
                        'Provide concise, practical advice about crops, weather, and markets.'
                    ),
                },
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI service error: {e}")
        return "Sorry, I could not process your request at this time."
