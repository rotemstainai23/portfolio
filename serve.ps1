# ============================================================
#  Portfolio Dashboard Server — PowerShell Proxy
#  Run: powershell -ExecutionPolicy Bypass -File serve.ps1
#  Opens: http://localhost:5000
# ============================================================
param([int]$Port = 5000)

$root          = Split-Path -Parent $MyInvocation.MyCommand.Definition
$portfolioFile = Join-Path $root 'portfolio.json'

# ── Price cache (55s TTL) ────────────────────────────────────
$script:PriceCache = @{}
$script:CacheTime  = [DateTime]::MinValue
$CacheTTL          = 55

# ── Default portfolio — loaded from portfolio.json (seeded separately) ──

# ── Portfolio helpers ────────────────────────────────────────
function Load-Portfolio {
    if (Test-Path $portfolioFile) {
        try {
            $raw = Get-Content $portfolioFile -Raw -Encoding UTF8
            return $raw | ConvertFrom-Json
        } catch { Write-Warning "Could not read portfolio.json: $_" }
    }
    # Return empty structure if file missing
    return [PSCustomObject]@{ cash=0; holdings=@(); trades=@() }
}

function Save-Portfolio($data) {
    $data | ConvertTo-Json -Depth 10 | Set-Content -Path $portfolioFile -Encoding UTF8
}

function Obj-To-Hashtable($obj) {
    # Recursively convert PSCustomObject → hashtable for easier manipulation
    if ($obj -is [System.Management.Automation.PSCustomObject]) {
        $ht = [ordered]@{}
        $obj.PSObject.Properties | ForEach-Object { $ht[$_.Name] = Obj-To-Hashtable $_.Value }
        return $ht
    } elseif ($obj -is [System.Collections.IEnumerable] -and $obj -isnot [string]) {
        return @($obj | ForEach-Object { Obj-To-Hashtable $_ })
    } else { return $obj }
}

# ── Yahoo Finance price fetch (v8 chart API — no auth needed) ─
function Get-SinglePrice([string]$sym, [hashtable]$headers) {
    # Yahoo Finance v8 chart API — no crumb/cookie required
    foreach ($apiHost in @('query1','query2')) {
        try {
            $url  = "https://$apiHost.finance.yahoo.com/v8/finance/chart/$([Uri]::EscapeDataString($sym))?interval=1d&range=2d&includePrePost=false"
            $resp = Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 8 -ErrorAction Stop
            $meta = $resp.chart.result[0].meta
            $curr = [double]$meta.regularMarketPrice
            $prev = if ($meta.PSObject.Properties['previousClose'] -and $meta.previousClose) {
                        [double]$meta.previousClose
                    } elseif ($meta.PSObject.Properties['chartPreviousClose']) {
                        [double]$meta.chartPreviousClose
                    } else { $null }
            $chg  = if ($curr -and $prev -and $prev -gt 0) { ($curr - $prev) / $prev * 100 } else { $null }
            return @{ price=$curr; chg=$chg; name=[string]$meta.shortName }
        } catch { }
    }
    return $null
}

function Get-Prices([string[]]$symbols) {
    $now = [DateTime]::Now
    if (($now - $script:CacheTime).TotalSeconds -lt $CacheTTL -and $script:PriceCache.Count -gt 0) {
        return $script:PriceCache
    }

    $headers = @{
        'User-Agent'      = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0'
        'Accept'          = 'application/json, text/plain, */*'
        'Accept-Language' = 'en-US,en;q=0.9'
        'Cache-Control'   = 'no-cache'
    }

    $results  = @{}
    $ts       = [DateTime]::Now.ToString('HH:mm:ss')
    $fetched  = [System.Collections.ArrayList]@()
    $failed   = [System.Collections.ArrayList]@()

    foreach ($sym in $symbols) {
        $data = Get-SinglePrice $sym $headers
        if ($data -and $data.price) {
            $results[$sym] = $data
            [void]$fetched.Add($sym)
        } else {
            $results[$sym] = @{ price=$null; chg=$null; name=$sym }
            [void]$failed.Add($sym)
        }
    }

    if ($fetched.Count -gt 0) {
        Write-Host "  [$ts] OK: $($fetched -join ', ')" -ForegroundColor Green
    }
    if ($failed.Count -gt 0) {
        Write-Host "  [$ts] N/A: $($failed -join ', ')" -ForegroundColor Yellow
    }

    $script:PriceCache = $results
    $script:CacheTime  = $now
    return $results
}

# ── Build enriched portfolio JSON ────────────────────────────
function Build-PortfolioJson {
    $p      = Load-Portfolio
    $hlist  = @(if ($p.holdings) { $p.holdings } else { @() })
    $wlist  = @(if ($p.watchlist) { $p.watchlist } else { @() })
    $syms   = @(@($hlist | ForEach-Object { $_.symbol }) + @($wlist | ForEach-Object { $_.symbol }) | Where-Object { $_ } | Select-Object -Unique)
    $prices = if ($syms.Count -gt 0) { Get-Prices $syms } else { @{} }

    $enriched   = [System.Collections.ArrayList]@()
    $totalValue = 0.0
    $totalCost  = 0.0
    $todayChg   = 0.0

    foreach ($h in $hlist) {
        $sym  = $h.symbol
        $pr   = $prices[$sym]
        $curr = if ($pr -and $pr.price) { [double]$pr.price } else { $null }
        $chg  = if ($pr -and $pr.chg  ) { [double]$pr.chg   } else { $null }
        $cost = [double]$h.buy_price * [double]$h.quantity
        $mval = if ($curr) { $curr * [double]$h.quantity } else { $null }
        $pnl  = if ($mval) { $mval - $cost } else { $null }
        $pnlP = if ($pnl -ne $null -and $cost -gt 0) { $pnl / $cost * 100 } else { $null }

        if ($mval)  { $totalValue += $mval  }
        $totalCost += $cost
        if ($curr -and $chg) {
            $prev      = $curr / (1 + $chg / 100)
            $todayChg += ($curr - $prev) * [double]$h.quantity
        }

        $row = [ordered]@{
            symbol        = $sym
            name          = if ($h.name)          { $h.name }          else { $sym }
            quantity      = [double]$h.quantity
            buy_price     = [double]$h.buy_price
            current_price = $curr
            day_change_pct= $chg
            market_value  = if ($mval) { [Math]::Round($mval,4) } else { $null }
            cost_basis    = [Math]::Round($cost,4)
            pnl           = if ($pnl)  { [Math]::Round($pnl, 4) } else { $null }
            pnl_pct       = if ($pnlP) { [Math]::Round($pnlP,4) } else { $null }
            layer         = $h.layer
            sector        = $h.sector
            analyst_score = $h.analyst_score
            risk_score    = $h.risk_score
            notes         = $h.notes
        }
        [void]$enriched.Add($row)
    }

    $cash    = if ($p.cash) { [double]$p.cash } else { 0 }
    $pnlTot  = $totalValue - $totalCost
    $trades  = @(if ($p.trades) { $p.trades } else { @() })

    # ── Enrich watchlist with live prices + alert flags ──
    $wenriched = [System.Collections.ArrayList]@()
    foreach ($w in $wlist) {
        $wpr   = $prices[$w.symbol]
        $wcurr = if ($wpr -and $wpr.price) { [double]$wpr.price } else { $null }
        $trig  = if ($w.trigger_price) { [double]$w.trigger_price } else { $null }
        $dir   = if ($w.trigger_direction) { [string]$w.trigger_direction } else { 'below' }
        $alert = $false
        if (($null -ne $wcurr) -and ($null -ne $trig)) {
            if ($dir -eq 'below' -and $wcurr -le $trig) { $alert = $true }
            if ($dir -eq 'above' -and $wcurr -ge $trig) { $alert = $true }
        }
        $wdist = if (($null -ne $wcurr) -and ($null -ne $trig) -and $trig -gt 0) { [Math]::Round(($wcurr - $trig) / $trig * 100, 2) } else { $null }
        $wrow = Obj-To-Hashtable $w
        $wrow['current_price'] = if ($null -ne $wcurr) { [Math]::Round($wcurr, 2) } else { $null }
        $wrow['distance_pct']  = $wdist
        $wrow['alert']         = $alert
        [void]$wenriched.Add($wrow)
    }

    return [ordered]@{
        holdings  = $enriched.ToArray()
        watchlist = $wenriched.ToArray()
        trades    = $trades
        cash      = $cash
        summary  = [ordered]@{
            total_value    = [Math]::Round($totalValue,4)
            total_cost     = [Math]::Round($totalCost, 4)
            total_pnl      = [Math]::Round($pnlTot,   4)
            total_pnl_pct  = if ($totalCost -gt 0) { [Math]::Round($pnlTot/$totalCost*100,4) } else { 0 }
            today_change   = [Math]::Round($todayChg, 4)
            grand_total    = [Math]::Round($totalValue+$cash,4)
            positions      = $enriched.Count
            trades_logged  = $trades.Count
        }
        timestamp = [DateTime]::Now.ToString('o')
    }
}

# ── HTTP helpers ─────────────────────────────────────────────
function Send-Json($res, $obj, [int]$status=200) {
    $json  = $obj | ConvertTo-Json -Depth 12 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $res.StatusCode      = $status
    $res.ContentType     = 'application/json; charset=utf-8'
    $res.ContentLength64 = $bytes.Length
    $res.OutputStream.Write($bytes, 0, $bytes.Length)
}

function Send-File($res, [string]$filePath) {
    $bytes = [System.IO.File]::ReadAllBytes($filePath)
    $ext   = [System.IO.Path]::GetExtension($filePath).ToLower()
    $res.ContentType     = switch($ext){ '.html'{'text/html; charset=utf-8'} '.json'{'application/json'} default{'text/plain'} }
    $res.ContentLength64 = $bytes.Length
    $res.OutputStream.Write($bytes, 0, $bytes.Length)
}

function Read-Body($req) {
    $reader = New-Object System.IO.StreamReader($req.InputStream, [System.Text.Encoding]::UTF8)
    return $reader.ReadToEnd()
}

function Add-CorsHeaders($res) {
    $res.Headers.Add('Access-Control-Allow-Origin','*')
    $res.Headers.Add('Access-Control-Allow-Methods','GET,POST,PUT,DELETE,OPTIONS')
    $res.Headers.Add('Access-Control-Allow-Headers','Content-Type')
}

# ── Start server ─────────────────────────────────────────────
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  Portfolio Dashboard — Server Running   ║" -ForegroundColor Cyan
Write-Host "  ╠══════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "  ║  Dashboard  :  http://localhost:$Port      ║" -ForegroundColor Green
Write-Host "  ║  Agent API  :  /api/portfolio            ║" -ForegroundColor Yellow
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Auto-open browser
Start-Process "http://localhost:$Port"

# ── Request loop ─────────────────────────────────────────────
while ($listener.IsListening) {
    try {
        $ctx    = $listener.GetContext()
        $req    = $ctx.Request
        $res    = $ctx.Response
        $method = $req.HttpMethod
        $path   = $req.Url.LocalPath.TrimEnd('/')

        Add-CorsHeaders $res

        # Preflight
        if ($method -eq 'OPTIONS') { $res.StatusCode = 204; $res.Close(); continue }

        Write-Host "  $method $path" -ForegroundColor DarkGray

        switch -regex ($path) {

            '^$|^/$' {
                Send-File $res (Join-Path $root 'portfolio.html')
            }

            '^/api/ping$' {
                Send-Json $res @{ ok=$true; mode='server'; time=[DateTime]::Now.ToString('HH:mm:ss') }
            }

            '^/api/chart$' {
                # Server-side proxy for Yahoo Finance OHLCV — avoids browser CORS
                $sym = $req.QueryString['symbol'];   if (-not $sym) { $sym = 'V' }
                $iv  = $req.QueryString['interval']; if (-not $iv)  { $iv  = '1d' }
                $rg  = $req.QueryString['range'];    if (-not $rg)  { $rg  = '6mo' }
                $chHeaders = @{
                    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0'
                    'Accept'     = 'application/json'
                }
                $body = $null
                foreach ($apiHost in @('query1','query2')) {
                    if ($body) { break }
                    try {
                        $cu = "https://$apiHost.finance.yahoo.com/v8/finance/chart/$([Uri]::EscapeDataString($sym))?interval=$iv&range=$rg"
                        $wr = Invoke-WebRequest -Uri $cu -Headers $chHeaders -TimeoutSec 12 -UseBasicParsing
                        $body = $wr.Content
                    } catch { }
                }
                if ($body) {
                    $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
                    $res.StatusCode      = 200
                    $res.ContentType     = 'application/json; charset=utf-8'
                    $res.ContentLength64 = $bytes.Length
                    $res.OutputStream.Write($bytes, 0, $bytes.Length)
                } else {
                    Send-Json $res @{ error='yahoo fetch failed' } 502
                }
            }

            '^/api/portfolio$' {
                $data = Build-PortfolioJson
                Send-Json $res $data
            }

            '^/api/holdings$' {
                if ($method -eq 'GET') {
                    $p = Load-Portfolio
                    Send-Json $res @(if ($p.holdings) { $p.holdings } else { @() })
                }
                elseif ($method -eq 'POST') {
                    $body = Read-Body $req | ConvertFrom-Json
                    $sym  = $body.symbol.ToUpper()
                    $p    = Obj-To-Hashtable (Load-Portfolio)
                    if (-not $p.holdings) { $p['holdings'] = @() }
                    $holdings = [System.Collections.ArrayList]@($p.holdings)
                    $found    = $false
                    for ($i=0; $i -lt $holdings.Count; $i++) {
                        if ($holdings[$i].symbol -eq $sym) {
                            $holdings[$i] = Obj-To-Hashtable $body
                            $holdings[$i]['symbol'] = $sym
                            $found = $true; break
                        }
                    }
                    if (-not $found) {
                        $newH = Obj-To-Hashtable $body; $newH['symbol'] = $sym
                        [void]$holdings.Add($newH)
                    }
                    $p['holdings'] = $holdings.ToArray()
                    Save-Portfolio $p
                    $script:CacheTime = [DateTime]::MinValue  # invalidate price cache
                    Send-Json $res @{ ok=$true }
                }
            }

            '^/api/holdings/([^/]+)$' {
                $sym = $Matches[1].ToUpper()
                if ($method -eq 'DELETE') {
                    $p = Obj-To-Hashtable (Load-Portfolio)
                    $p['holdings'] = @($p.holdings | Where-Object { $_.symbol -ne $sym })
                    Save-Portfolio $p
                    Send-Json $res @{ ok=$true }
                }
            }

            '^/api/watchlist$' {
                if ($method -eq 'GET') {
                    $p = Load-Portfolio
                    Send-Json $res @(if ($p.watchlist) { $p.watchlist } else { @() })
                }
                elseif ($method -eq 'POST') {
                    $body = Read-Body $req | ConvertFrom-Json
                    $sym  = $body.symbol.ToUpper()
                    $p    = Obj-To-Hashtable (Load-Portfolio)
                    if (-not $p.watchlist) { $p['watchlist'] = @() }
                    $wl    = [System.Collections.ArrayList]@($p.watchlist)
                    $found = $false
                    for ($i=0; $i -lt $wl.Count; $i++) {
                        if ($wl[$i].symbol -eq $sym) {
                            $wl[$i] = Obj-To-Hashtable $body
                            $wl[$i]['symbol'] = $sym
                            $found = $true; break
                        }
                    }
                    if (-not $found) {
                        $newW = Obj-To-Hashtable $body; $newW['symbol'] = $sym
                        [void]$wl.Add($newW)
                    }
                    $p['watchlist'] = $wl.ToArray()
                    Save-Portfolio $p
                    $script:CacheTime = [DateTime]::MinValue
                    Send-Json $res @{ ok=$true }
                }
            }

            '^/api/watchlist/([^/]+)$' {
                $sym = $Matches[1].ToUpper()
                if ($method -eq 'DELETE') {
                    $p = Obj-To-Hashtable (Load-Portfolio)
                    $p['watchlist'] = @($p.watchlist | Where-Object { $_.symbol -ne $sym })
                    Save-Portfolio $p
                    Send-Json $res @{ ok=$true }
                }
            }

            '^/api/trades$' {
                if ($method -eq 'GET') {
                    $p = Load-Portfolio
                    Send-Json $res @(if ($p.trades) { $p.trades } else { @() })
                }
                elseif ($method -eq 'POST') {
                    $body   = Read-Body $req | ConvertFrom-Json
                    $p      = Obj-To-Hashtable (Load-Portfolio)
                    if (-not $p.trades) { $p['trades'] = @() }
                    $trades = [System.Collections.ArrayList]@($p.trades)
                    $lastN  = 0
                    if ($trades.Count -gt 0) {
                        $lastId = $trades[$trades.Count-1]
                        if ($lastId -and $lastId.trade_id) {
                            $lastN = [int]($lastId.trade_id -replace 'TRD-','')
                        }
                    }
                    $newT = Obj-To-Hashtable $body
                    $newT['trade_id'] = 'TRD-' + ($lastN+1).ToString('D3')
                    [void]$trades.Add($newT)
                    $p['trades'] = $trades.ToArray()
                    Save-Portfolio $p
                    Send-Json $res @{ ok=$true; trade_id=$newT.trade_id }
                }
            }

            '^/api/trades/(\d+)$' {
                $idx = [int]$Matches[1]
                if ($method -eq 'DELETE') {
                    $p = Obj-To-Hashtable (Load-Portfolio)
                    $arr = [System.Collections.ArrayList]@($p.trades)
                    if ($idx -ge 0 -and $idx -lt $arr.Count) { $arr.RemoveAt($idx) }
                    $p['trades'] = $arr.ToArray()
                    Save-Portfolio $p
                    Send-Json $res @{ ok=$true }
                }
            }

            '^/api/cash$' {
                if ($method -eq 'PUT') {
                    $body = Read-Body $req | ConvertFrom-Json
                    $p    = Obj-To-Hashtable (Load-Portfolio)
                    $p['cash'] = [double]$body.cash
                    Save-Portfolio $p
                    Send-Json $res @{ ok=$true }
                }
            }

            default {
                Send-Json $res @{ error='Not found' } 404
            }
        }

        $res.Close()

    } catch {
        Write-Warning "Request error: $_"
        try { $ctx.Response.Close() } catch {}
    }
}
