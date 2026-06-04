---
name: financial-statements
description: דוחות כספיים לחברה (Income Statement, Balance Sheet, Cash Flow) עם השוואה רב-תקופתית וניתוח variances. מוד תיק מציג P&L של התיק עצמו.
argument-hint: "<TICKER> [annual|quarterly]  OR  portfolio [monthly|quarterly]"
---

# /financial-statements

## שימוש

```
/financial-statements TICKER [annual|quarterly]
/financial-statements portfolio [monthly|quarterly]
```

## עיקרון: Token Efficiency

**סדר קריאה (מהזול לביקוע):**
1. קרא `analyses/<TICKER>/analyst.js` (דיסק, חינם) — financials_3y + quarterly לקונטקסט
2. קרא `GET /api/financial-statements/<TICKER>?period=...` — yfinance, לא LLM
3. פתח `http://127.0.0.1:5000/templates/financial_statements.html?ticker=TICKER&period=PERIOD`
4. **אל תריץ** מחדש את Unified_Analyst רק בגלל דוחות — הוא כבר נרץ

## מוד חברה: /financial-statements NVDA annual

1. בדוק אם analyst.js קיים: `analyses/NVDA/analyst.js`
2. קרא את ה-API: `GET /api/financial-statements/NVDA?period=annual`
3. נתח את הפלט:
   - income_statement[0] = הכי עדכני. income_statement[1] = שנה קודמת
   - `.variances` מכיל YoY% לכל שורה
   - `.analyst_context.financials_3y` = מגמות 3 שנים מ-analyst.js
4. פתח את התבנית: `templates/financial_statements.html?ticker=NVDA&period=annual`
5. דגל משתנות מהותיות (>10% או >$500M) בדיווח לניתוח

## מוד תיק: /financial-statements portfolio monthly

1. קרא `GET /api/monthly-close/latest`
2. קרא `portfolio.json` — cost_basis, quantity לכל אחזקה
3. הצג P&L:
   - רווח לא-ממומש לפי שכבה (Growth/Stability/Speculation/Cash)
   - תזרים הון (קניות/מכירות מ-trades)
   - תשואה כוללת vs. חודש קודם
4. פתח: `templates/financial_statements.html?mode=portfolio&period=monthly`

## גבולות

- לא מפעיל מחדש שרשרת סוכנים
- לא משנה portfolio.json, decision_log.json, agent schemas
- כל הנתונים קוראים בלבד (read-only)
- yfinance חינמי, ללא API key, ללא עלות
