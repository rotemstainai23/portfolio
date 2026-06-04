---
name: monthly-close
description: דוח סגירה חודשי — P&L, thesis review, ביצועי ראדר, כיול סורק. מריץ אגרגציה ללא LLM call. שימוש: /monthly-close או "סגירת חודש" או "דוח חודשי".
user-invocable: true
---

# /monthly-close

דוח סגירה חודשי לתיק ההשקעות. אין API calls — Python טהור + דשבורד.

## טריגרים
- `/monthly-close`
- `/monthly-close 2026-05` (חודש ספציפי)
- "סגירת חודש" | "דוח חודשי" | "monthly review"

## זרימה (7 שלבים)

### שלב 1 — קבע period
- ללא ארגומנט: החודש הנוכחי (`YYYY-MM`)
- עם ארגומנט: השתמש בו כ-period

### שלב 2 — הרץ monthly_close.py
```powershell
cd "C:\Users\רותם\portfolio"
python scripts\monthly_close.py <period>
```
הסקריפט כותב:
- `analyses/_monthly/<period>/monthly_close.js`
- `analyses/_monthly/<period>/scanner_calibration.json`

### שלב 3 — אמת פלט
בדוק שהקובץ נוצר:
```powershell
Test-Path "C:\Users\רותם\portfolio\analyses\_monthly\<period>\monthly_close.js"
```

### שלב 4 — הצג סיכום
הדפס לממשק:
- שינוי חודשי תיק (month_pct)
- Thesis Score
- Hit Rate ראדר (אם יש)
- מספר החלטות החודש

### שלב 5 — פתח דשבורד
```
http://127.0.0.1:5000/templates/monthly.html?period=<period>
```

### שלב 6 — דגלי אזהרה (run only if data present)
בדוק ב-monthly_close.js:
- אחזקות עם `ic_verdict` = REDUCE/SELL/EXIT → הצג התראה
- ניתוחים עם freshness = 'red' (>45 ימים) → הצג רשימה
- allocation drift > 8% בשכבה כלשהי → הצג אזהרה

### שלב 7 — דווח
סיכום קצר (5 שורות מקסימום):
- תאריך, period
- ביצועים חודשיים
- Thesis Score
- Hit Rate ראדר
- פעולות נדרשות

## כללים
- אין LLM call נוסף — pure Python.
- אסור לגעת ב-portfolio.json, handoff schemas, *.js ניתוחים קיימים.
- שגיאה ב-monthly_close.py → הצג output מלא ועצור.
- אם Flask לא רץ — הדשבורד עדיין נגיש דרך קובץ ישיר (open-file).

## קשר ל-close-management
הסקיל `close-management` (גלובלי) מגדיר את מסגרת 5-הימים.
monthly-close מיישם אותה לתיק השקעות:
- T+1 = P&L + positions
- T+2 = Thesis Reconciliation
- T+3 = Allocation Reconciliation
- T+4 = החלטות + freshness
- T+5 = Scanner Performance + close + agenda
