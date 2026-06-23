"""הגדרות מרכזיות. טוען משתני סביבה מקובץ .env (פרסר מינימלי, ללא תלות חיצונית)."""
from __future__ import annotations

import logging
import os
import ssl
from pathlib import Path

# נתיבי בסיס
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "barebone.db"


def _load_dotenv(path: Path) -> None:
    """טעינה פשוטה של קובץ .env לתוך os.environ (לא דורס ערכים קיימים)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

# SEC EDGAR מחייב User-Agent עם אימייל. ברירת מחדל בטוחה אם לא הוגדר.
SEC_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT", "Barebone.AI research rotemstain23@gmail.com"
)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # ponytail: לא בשימוש, ה-LLM הוא Groq
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"  # סינתזה/הסבר חינמי דרך Groq

# מודלים: כבד לסינתזה, קל למשימות פשוטות. הסבר/סינתזה בלבד, לעולם לא חישוב מספרים.
LLM_MODEL_HEAVY = "claude-opus-4-8"
LLM_MODEL_LIGHT = "claude-haiku-4-5-20251001"

# מדיניות cache (שניות)
CACHE_TTL_DEFAULT = 60 * 60 * 6  # 6 שעות לנתונים פונדמנטליים
CACHE_TTL_PRICE = 60 * 15  # 15 דקות למחירים

# קצב בקשות ל-SEC (מקסימום ~10/שנייה לפי הנחיות SEC; שומרים שוליים)
SEC_MIN_INTERVAL = 0.2  # שנייה בין בקשות

# יצירת תיקיות נתונים
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _install_tls_trust() -> None:
    """מתאים את אימות ה-TLS לסביבות עם SSL interception (אנטי-וירוס/פרוקסי).

    שתי בעיות נפתרות:
    1. requests/ssl: שורש היירוט אינו ב-certifi, ותעודות ה-MITM נופלות באימות
       המחמיר של OpenSSL 3. הפתרון: truststore - מאציל אימות למאגר של Windows
       (אותו מנגנון שבו משתמש pip), שכבר סומך על שורש היירוט וסלחני יותר.
    2. curl_cffi (yfinance): אינו עובר דרך ssl של פייתון. מפנים אותו ל-bundle משולב
       (certifi + שורשי Windows) דרך CURL_CA_BUNDLE.
    """
    # 1. truststore עבור requests/urllib3
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception as exc:  # אסור שכשל יפיל אתחול
        logging.getLogger("barebone").warning("הזרקת truststore נכשלה: %s", exc)

    # 2. bundle משולב עבור curl_cffi
    bundle = DATA_DIR / "ca_bundle.pem"
    try:
        import certifi

        parts = [Path(certifi.where()).read_text(encoding="utf-8")]
        for store in ("ROOT", "CA"):
            try:
                for cert, enc, _ in ssl.enum_certificates(store):
                    if enc == "x509_asn":
                        parts.append(ssl.DER_cert_to_PEM_cert(cert))
            except (OSError, ssl.SSLError):
                continue
        bundle.write_text("\n".join(parts), encoding="utf-8")
        os.environ["CURL_CA_BUNDLE"] = str(bundle)
    except Exception as exc:
        logging.getLogger("barebone").warning("בניית CA bundle ל-curl נכשלה: %s", exc)


_install_tls_trust()

# לוגינג מרכזי
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("barebone")
