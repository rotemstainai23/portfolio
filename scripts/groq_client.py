"""
לקוח Groq משותף לכל סקריפטי הדיווח.
sanitization של JSON עברי + חילוץ array מרכזיים כאן.
"""
import json
import os
import re

import requests

GROQ_URL   = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'


def call_groq(system, user, max_tokens=600, temperature=0.3, timeout=45):
    """
    שולח system+user ל-Groq. מחזיר את תוכן התשובה כ-string, או '' בכישלון.
    """
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        return ''
    try:
        resp = requests.post(
            GROQ_URL,
            headers={'Authorization': f'Bearer {api_key}',
                     'Content-Type':  'application/json'},
            json={
                'model':       GROQ_MODEL,
                'messages':    [
                    {'role': 'system', 'content': system},
                    {'role': 'user',   'content': user},
                ],
                'max_tokens':  max_tokens,
                'temperature': temperature,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[groq] שגיאה: {e}')
        return ''


def extract_json_array(raw):
    """
    מחלץ JSON array מתוך תשובת Groq (שעלולה לכלול טקסט נוסף).
    כולל sanitization של גרשיים עבריים שוברי JSON.
    מחזיר list (אלמנטים כמו שהם — string, dict, etc.), או [] בכישלון.
    """
    if not raw:
        return []
    start = raw.find('[')
    end   = raw.rfind(']')
    if start == -1 or end == -1 or end < start:
        return []
    raw = raw[start:end+1]
    raw = re.sub(r'(?<=[^\s,:{"\[])\"(?=[^\s,}:\]\[])', '', raw)
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return [r for r in result if r is not None]
        return []
    except Exception:
        return []
