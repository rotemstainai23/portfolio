"""
מודול התראות: ntfy.sh (push notification חינמי לטלפון).

הגדרה חד-פעמית:
1. הורד אפליקציית "ntfy" לטלפון (iOS / Android)
2. לחץ "Subscribe to topic" ובחר שם סודי, לדוגמה: rotem-portfolio-xyz123
3. מלא notifications_config.json עם ntfy_topic

אפשרות גיבוי: CallMeBot WhatsApp — אם ntfy_topic מוגדר, ntfy קודם.
"""
import json
import os
import urllib.parse
import urllib.request

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'notifications_config.json')


def _load_cfg() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, encoding='utf-8-sig') as f:
        return json.load(f)


# ── ntfy.sh ──────────────────────────────────────────────────────────────────

def send_ntfy(message: str, title: str = 'מערכת ההשקעות', priority: int = 3,
              tags: list | None = None, click_url: str = '') -> bool:
    """שלח push notification דרך ntfy.sh. חינמי, ללא חשבון."""
    cfg   = _load_cfg()
    topic = cfg.get('ntfy_topic') or os.environ.get('NTFY_TOPIC')
    if not topic:
        print('[notifications] ntfy_topic לא מוגדר')
        return False
    try:
        url     = f'https://ntfy.sh/{topic}'
        headers = {
            'Title':    title.encode('utf-8'),
            'Priority': str(priority),
            'Content-Type': 'text/plain; charset=utf-8',
        }
        if tags:
            headers['Tags'] = ','.join(tags)
        if click_url:
            headers['Click'] = click_url
        data = message.encode('utf-8')
        req  = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            ok = r.status == 200
        if ok:
            print(f'[notifications] ntfy: נשלח ל-{topic}')
        return ok
    except Exception as e:
        print(f'[notifications] ntfy שגיאה: {e}')
        return False


# ── WhatsApp CallMeBot (גיבוי) ───────────────────────────────────────────────

def send_whatsapp(message: str) -> bool:
    """גיבוי: שלח לוואצאפ דרך CallMeBot."""
    cfg     = _load_cfg()
    phone   = cfg.get('whatsapp_phone') or os.environ.get('WHATSAPP_PHONE')
    api_key = cfg.get('callmebot_apikey') or os.environ.get('CALLMEBOT_APIKEY')
    if not phone or not api_key:
        return False
    try:
        encoded = urllib.parse.quote(message)
        url     = (f'https://api.callmebot.com/whatsapp.php'
                   f'?phone={phone}&text={encoded}&apikey={api_key}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        print(f'[notifications] WhatsApp שגיאה: {e}')
        return False


# ── ממשק מאוחד ───────────────────────────────────────────────────────────────

def send_notification(message: str, title: str = 'מערכת ההשקעות',
                      tags: list | None = None, click_url: str = '') -> dict:
    """שלח התראה — ntfy ראשון, וואצאפ כגיבוי אם ntfy נכשל."""
    cfg = _load_cfg()
    results = {}

    if cfg.get('ntfy_topic') or os.environ.get('NTFY_TOPIC'):
        results['ntfy'] = send_ntfy(message, title=title, tags=tags, click_url=click_url)
    if cfg.get('whatsapp_phone') or os.environ.get('WHATSAPP_PHONE'):
        # WhatsApp לא תומך בעיצוב — שלח גרסה נקייה
        clean = message.replace('*', '').replace('_', '').replace('`', '')
        results['whatsapp'] = send_whatsapp(clean)

    return results


def send_both(short_text: str, full_text: str | None = None) -> dict:
    """תאימות לאחור עם הסקריפטים הקיימים."""
    msg = full_text if full_text else short_text
    return send_notification(msg)


# ── כלי עזר ──────────────────────────────────────────────────────────────────

def save_config(ntfy_topic: str = '', whatsapp_phone: str = '',
                callmebot_apikey: str = '') -> None:
    cfg = _load_cfg()
    if ntfy_topic:
        cfg['ntfy_topic'] = ntfy_topic
    if whatsapp_phone:
        cfg['whatsapp_phone'] = whatsapp_phone
    if callmebot_apikey:
        cfg['callmebot_apikey'] = callmebot_apikey
    with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f'[notifications] נשמר: {_CONFIG_PATH}')


def test_notifications() -> None:
    """בדיקת שליחה — הרץ מה-terminal."""
    result = send_notification(
        message='מערכת ההשקעות — בדיקת חיבור OK\nאם קיבלת את זה, ההתראות פועלות.',
        title='בדיקה',
        tags=['white_check_mark'],
    )
    print(f'תוצאה: {result}')


if __name__ == '__main__':
    test_notifications()
