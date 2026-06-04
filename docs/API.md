# API.md

Backend implementation:
`serve.ps1`

Purpose:
Native PowerShell HTTP server (`.NET HttpListener`) serving:

- Dashboard UI
- REST API
- Yahoo Finance proxy
- Portfolio management endpoints

Server startup:

```powershell
powershell -ExecutionPolicy Bypass -File portfolio\serve.ps1
```

Health check:

```powershell
curl http://localhost:5000/api/ping
```

Important:
- `app.py` is deprecated
- `start.bat` is deprecated
- Use `serve.ps1` only
- Restart required after editing `serve.ps1` (no hot reload)

---

# API Endpoints

## Dashboard

| Path | Method | Purpose |
|------|--------|----------|
| `/` | GET | Serves `portfolio.html` |

---

## Portfolio

| Path | Method | Purpose |
|------|--------|----------|
| `/api/portfolio` | GET | Returns enriched portfolio with live prices, P&L, and watchlist alerts |

Notes:
- This is the primary endpoint consumed by agents.
- Returns live-enriched portfolio state.

---

## Yahoo Finance Proxy

| Path | Method | Purpose |
|------|--------|----------|
| `/api/chart?symbol=&interval=&range=` | GET | Yahoo Finance v8 proxy (browser CORS workaround) |

Yahoo source:

```text
query1.finance.yahoo.com/v8/finance/chart
query2.finance.yahoo.com/v8/finance/chart
```

Notes:
- No authentication required
- Cache duration: 55 seconds

---

## Holdings

| Path | Method | Purpose |
|------|--------|----------|
| `/api/holdings` | GET | Retrieve holdings |
| `/api/holdings` | POST | Add/update holding |
| `/api/holdings/{sym}` | DELETE | Remove holding |

Important:
POST/DELETE automatically reset cache.

---

## Watchlist

| Path | Method | Purpose |
|------|--------|----------|
| `/api/watchlist` | GET | Retrieve watchlist |
| `/api/watchlist` | POST | Add/update watchlist item |
| `/api/watchlist/{sym}` | DELETE | Remove watchlist item |

Important:
Watchlist supports:

- `trigger_price`
- `trigger_direction`

Valid trigger directions:

```text
below
above
```

POST/DELETE automatically reset cache.

---

## Trades

| Path | Method | Purpose |
|------|--------|----------|
| `/api/trades` | GET | Retrieve trade log |
| `/api/trades` | POST | Add trade |
| `/api/trades/{idx}` | DELETE | Remove trade |

Trade IDs auto-generated:

```text
TRD-001
TRD-002
TRD-003
```

---

## Cash

| Path | Method | Purpose |
|------|--------|----------|
| `/api/cash` | PUT | Update cash balance |

---

## Health

| Path | Method | Purpose |
|------|--------|----------|
| `/api/ping` | GET | Health check |

---

# Runtime Rules

When server is running:

Do NOT manually edit:

```text
portfolio.json
```

Use API instead.

Reason:
POST/DELETE reset cache automatically.

Manual edits during runtime may result in stale price data.
