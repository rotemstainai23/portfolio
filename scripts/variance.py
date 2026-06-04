"""
מנוע ייחוס variance — חישוב attribution טהור, ללא LLM.
משמש monthly_close.py ואת הסקיל /variance-analysis.

כל הפונקציות מקבלות structures מ-monthly_close.py ומחזירות dicts
שנכנסים ל-monthly_close.js תחת מפתח 'variance'.
"""


def holding_attribution(holdings_monthly: list, total_value: float) -> list:
    """
    contribution של כל מניה לתשואה החודשית (נקודות אחוז של תיק).
    contribution_pp = (chg_month_pct / 100) × weight × 100
    מוחזר מסודר מגדול לקטן.
    """
    if not total_value:
        return []

    result = []
    for h in holdings_monthly:
        chg      = h.get('chg_month_pct') or 0
        curr_val = h.get('current_value') or 0
        weight   = curr_val / total_value
        contrib  = (chg / 100) * weight * 100
        result.append({
            'ticker':          h['ticker'],
            'layer':           h.get('layer', ''),
            'weight_pct':      round(weight * 100, 1),
            'chg_month_pct':   round(chg, 2),
            'contribution_pp': round(contrib, 2),
        })

    result.sort(key=lambda x: x['contribution_pp'], reverse=True)
    return result


def layer_attribution(holding_attr: list) -> dict:
    """מרכז contribution לפי שכבה (Growth / Stability / Speculation / אחר)."""
    layers: dict = {}
    for h in holding_attr:
        layer = h.get('layer') or 'Other'
        if layer not in layers:
            layers[layer] = {'contribution_pp': 0.0, 'weight_pct': 0.0, 'tickers': []}
        layers[layer]['contribution_pp'] = round(
            layers[layer]['contribution_pp'] + h['contribution_pp'], 2
        )
        layers[layer]['weight_pct'] = round(
            layers[layer]['weight_pct'] + h['weight_pct'], 1
        )
        layers[layer]['tickers'].append(h['ticker'])
    return layers


def allocation_variance(holdings_monthly: list, portfolio: dict) -> dict:
    """
    מפרק drift בהקצאה לשכבות לשני גורמים:
      price_effect  — כמה ה-allocation זז בגלל תנועות שוק (פסיבי)
      volume_effect — כמה ה-allocation זז בגלל קניות/מכירות (אקטיבי)

    total_drift = price_effect + volume_effect
    """
    layer_targets = {'Growth': 40, 'Stability': 35, 'Speculation': 15, 'Cash': 10}
    cash = portfolio.get('cash', 0)

    total_at_cost  = sum(h.get('cost_basis', 0)     for h in holdings_monthly) + cash
    total_at_curr  = sum(h.get('current_value', 0)  for h in holdings_monthly) + cash

    if not total_at_cost or not total_at_curr:
        return {}

    cost_by_layer: dict  = {}
    curr_by_layer: dict  = {}
    for h in holdings_monthly:
        layer = h.get('layer') or 'Other'
        cost_by_layer[layer] = cost_by_layer.get(layer, 0) + (h.get('cost_basis', 0) or 0)
        curr_by_layer[layer] = curr_by_layer.get(layer, 0) + (h.get('current_value', 0) or 0)
    cost_by_layer['Cash'] = cash
    curr_by_layer['Cash'] = cash

    result = {}
    all_layers = set(list(layer_targets.keys()) + list(curr_by_layer.keys()))
    for layer in all_layers:
        cost_pct   = round(cost_by_layer.get(layer, 0) / total_at_cost * 100, 1)
        actual_pct = round(curr_by_layer.get(layer, 0) / total_at_curr * 100, 1)
        target_pct = layer_targets.get(layer, 0)

        price_effect  = round(actual_pct - cost_pct, 1)     # שוק הזיז
        volume_effect = round(cost_pct - target_pct, 1)     # החלטה אקטיבית
        total_drift   = round(actual_pct - target_pct, 1)

        result[layer] = {
            'target_pct':     target_pct,
            'cost_pct':       cost_pct,
            'actual_pct':     actual_pct,
            'total_drift':    total_drift,
            'price_effect':   price_effect,
            'volume_effect':  volume_effect,
        }
    return result


def scanner_variance(current_stats: dict, prior_stats: dict) -> dict:
    """
    period-over-period delta בביצועי הסורק.
    current_stats / prior_stats = scanner_performance block מ-monthly_close.js
    """
    if not current_stats or not prior_stats:
        return {}

    curr_hr = current_stats.get('hit_rate_pct') or 0
    prev_hr = prior_stats.get('hit_rate_pct') or 0

    curr_conv = current_stats.get('by_conviction') or {}
    prev_conv = prior_stats.get('by_conviction') or {}
    conv_delta = {}
    for k in set(list(curr_conv.keys()) + list(prev_conv.keys())):
        c = curr_conv.get(k)
        p = prev_conv.get(k)
        if c is not None and p is not None:
            conv_delta[k] = round(float(c) - float(p), 1)

    return {
        'hit_rate_delta':    round(curr_hr - prev_hr, 1),
        'hit_rate_current':  curr_hr,
        'hit_rate_prior':    prev_hr,
        'avg_return_delta':  round(
            (current_stats.get('avg_return_pct') or 0) -
            (prior_stats.get('avg_return_pct') or 0), 2
        ),
        'conviction_delta':  conv_delta,
    }


def thesis_variance(current_adherence: dict, prior_adherence: dict) -> dict:
    """שינוי ב-thesis score period-over-period."""
    if not current_adherence or not prior_adherence:
        return {}

    curr = current_adherence.get('score_0_100') or 0
    prev = prior_adherence.get('score_0_100') or 0

    return {
        'score_delta':   round(curr - prev, 1),
        'score_current': curr,
        'score_prior':   prev,
        'intact_delta':  (current_adherence.get('intact') or 0) - (prior_adherence.get('intact') or 0),
        'drift_delta':   (current_adherence.get('drift')  or 0) - (prior_adherence.get('drift')  or 0),
        'broken_delta':  (current_adherence.get('broken') or 0) - (prior_adherence.get('broken') or 0),
    }


def build_variance_block(holdings_monthly: list, portfolio: dict,
                          scanner_perf: dict, thesis_summary: dict,
                          prior_monthly_data: dict) -> dict:
    """
    נקודת כניסה ראשית — מריץ את כל חישובי ה-variance ומחזיר block אחד
    לשילוב ב-monthly_close.js תחת מפתח 'variance'.
    """
    total_value = (
        sum(h.get('current_value', 0) for h in holdings_monthly) +
        portfolio.get('cash', 0)
    )

    h_attr   = holding_attribution(holdings_monthly, total_value)
    l_attr   = layer_attribution(h_attr)
    alloc_v  = allocation_variance(holdings_monthly, portfolio)

    prior_scanner = (prior_monthly_data or {}).get('scanner_performance', {})
    prior_thesis  = (prior_monthly_data or {}).get('thesis_adherence', {})

    sc_var = scanner_variance(scanner_perf, prior_scanner)
    th_var = thesis_variance(thesis_summary, prior_thesis)

    return {
        'holding_attribution': h_attr,
        'layer_attribution':   l_attr,
        'allocation_variance': alloc_v,
        'scanner_variance':    sc_var,
        'thesis_variance':     th_var,
    }
