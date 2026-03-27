"""
QA Analyzer — PulseSignal Pro
Converts stored signal data (score_breakdown, mtf_analysis) into
human-readable research logs for the internal testing zone.
"""
from __future__ import annotations
from typing import Optional
import json


# ── Indicator category labels ──────────────────────────────────────────────
CATEGORY_LABELS = {
    'ict': 'ICT Smart Money',
    'structure': 'Market Structure',
    'trend': 'Trend',
    'momentum': 'Momentum',
    'volatility': 'Volatility',
    'volume': 'Volume',
    'fibonacci': 'Fibonacci',
}

# Minimum score fraction (0-1) to consider a category "confirming"
CATEGORY_CONFIRMATION_THRESHOLD = 0.5


def analyze_signal(
    score_breakdown: dict,
    mtf_analysis: dict,
    confidence: int,
    direction: str,
    timeframe: str,
    symbol: str,
    entry: float,
    stop_loss: float,
    take_profit_1: float,
    take_profit_2: float,
    rr_ratio: float,
    status: str = 'active',
    pnl_pct: Optional[float] = None,
) -> dict:
    """
    Produce a structured QA research record for a single signal.

    Returns a dict with:
      - why_generated: str  — plain English summary
      - confirmations_present: list[str]
      - confirmations_missing: list[str]
      - mtf_summary: dict
      - category_scores: dict
      - strength_assessment: str
      - risk_assessment: str
      - outcome_summary: str (if resolved)
    """

    # ── Parse category scores ──────────────────────────────────────────────
    category_totals: dict[str, dict] = {}
    triggered_indicators: list[str] = []
    missing_indicators: list[str] = []

    for ind_name, ind_data in score_breakdown.items():
        score = ind_data.get('score', 0)
        max_score = ind_data.get('max_score', 1)
        triggered = ind_data.get('triggered', False)
        details = ind_data.get('details', '')

        # Determine category from name prefix
        cat = _guess_category(ind_name)
        if cat not in category_totals:
            category_totals[cat] = {'score': 0, 'max': 0, 'triggered_count': 0, 'total_count': 0}

        category_totals[cat]['score'] += score
        category_totals[cat]['max'] += max_score
        category_totals[cat]['total_count'] += 1
        if triggered:
            category_totals[cat]['triggered_count'] += 1
            triggered_indicators.append(f"{_format_name(ind_name)} ({score}/{max_score})")
        else:
            missing_indicators.append(_format_name(ind_name))

    # ── Category confirmation list ─────────────────────────────────────────
    confirmations_present = []
    confirmations_missing = []
    category_scores = {}
    for cat, totals in category_totals.items():
        label = CATEGORY_LABELS.get(cat, cat.title())
        frac = totals['score'] / totals['max'] if totals['max'] > 0 else 0
        pct = round(frac * 100)
        category_scores[label] = {
            'score': totals['score'],
            'max': totals['max'],
            'pct': pct,
            'triggered': totals['triggered_count'],
            'total': totals['total_count'],
        }
        if frac >= CATEGORY_CONFIRMATION_THRESHOLD:
            confirmations_present.append(f"{label} ({pct}%)")
        else:
            confirmations_missing.append(f"{label} ({pct}%)")

    # ── MTF alignment summary ──────────────────────────────────────────────
    mtf_summary = {}
    aligned_tfs = []
    conflicting_tfs = []
    for tf, tf_data in mtf_analysis.items():
        aligned = tf_data.get('aligned', False)
        long_c = tf_data.get('long_confidence', 0)
        short_c = tf_data.get('short_confidence', 0)
        mtf_summary[tf] = {
            'aligned': aligned,
            'long_confidence': long_c,
            'short_confidence': short_c,
            'bias': 'LONG' if long_c > short_c else 'SHORT',
        }
        if aligned:
            aligned_tfs.append(tf)
        else:
            conflicting_tfs.append(tf)

    tf_5m_ok = '5m' in aligned_tfs
    tf_15m_ok = '15m' in aligned_tfs
    tf_1h_ok = '1H' in aligned_tfs
    tf_4h_ok = '4H' in aligned_tfs

    # ── Why generated ─────────────────────────────────────────────────────
    conf_band = _confidence_band(confidence)
    reason_parts = [
        f"{direction} signal on {symbol} ({timeframe}) with {confidence}% confidence ({conf_band}).",
    ]

    if confirmations_present:
        reason_parts.append(f"Confirmed by: {', '.join(confirmations_present[:5])}.")
    if aligned_tfs:
        reason_parts.append(f"HTF alignment: {', '.join(sorted(aligned_tfs))}.")
    if conflicting_tfs:
        reason_parts.append(f"Conflicting timeframes: {', '.join(sorted(conflicting_tfs))}.")
    if not tf_5m_ok and '5m' in mtf_analysis:
        reason_parts.append("WARNING: 5m not aligned.")
    if not tf_15m_ok and '15m' in mtf_analysis:
        reason_parts.append("WARNING: 15m not aligned.")

    why_generated = ' '.join(reason_parts)

    # ── Strength assessment ────────────────────────────────────────────────
    if confidence >= 90:
        strength = "ULTRA STRONG — near-perfect confluence across all systems"
    elif confidence >= 80:
        strength = "STRONG — high confluence, most indicators aligned"
    elif confidence >= 75:
        strength = "SOLID — minimum qualifying threshold met, multiple confirmations"
    else:
        strength = "WEAK — below quality threshold (should not have been generated)"

    # ── Risk assessment ───────────────────────────────────────────────────
    if stop_loss > 0 and entry > 0:
        risk_pct = abs(entry - stop_loss) / entry * 100
        if rr_ratio >= 3.0:
            risk_note = f"Excellent RR ({rr_ratio:.1f}R), risk {risk_pct:.2f}% to SL"
        elif rr_ratio >= 2.0:
            risk_note = f"Good RR ({rr_ratio:.1f}R), risk {risk_pct:.2f}% to SL"
        else:
            risk_note = f"Low RR ({rr_ratio:.1f}R) — marginal setup, risk {risk_pct:.2f}% to SL"
    else:
        risk_note = "SL not set"

    # ── Outcome summary ───────────────────────────────────────────────────
    if status in ('tp1_hit', 'tp2_hit', 'tp3_hit'):
        tp_num = status[2]
        outcome = f"WIN — TP{tp_num} hit. PnL: {pnl_pct:+.2f}%" if pnl_pct is not None else f"WIN — TP{tp_num} hit"
    elif status == 'sl_hit':
        outcome = f"LOSS — SL hit. PnL: {pnl_pct:+.2f}%" if pnl_pct is not None else "LOSS — SL hit"
    elif status == 'expired':
        outcome = "EXPIRED — price did not reach TP or SL within signal window"
    elif status == 'active':
        outcome = "ACTIVE — signal still open"
    else:
        outcome = f"STATUS: {status}"

    return {
        'why_generated': why_generated,
        'confirmations_present': confirmations_present,
        'confirmations_missing': confirmations_missing,
        'triggered_indicators': triggered_indicators[:10],
        'missing_indicators': missing_indicators[:10],
        'mtf_summary': mtf_summary,
        'aligned_tfs': aligned_tfs,
        'conflicting_tfs': conflicting_tfs,
        'tf_5m_confirmed': tf_5m_ok,
        'tf_15m_confirmed': tf_15m_ok,
        'tf_1h_confirmed': tf_1h_ok,
        'tf_4h_confirmed': tf_4h_ok,
        'category_scores': category_scores,
        'strength_assessment': strength,
        'risk_assessment': risk_note,
        'outcome_summary': outcome,
        'confirmation_count': len(confirmations_present),
        'missing_count': len(confirmations_missing),
    }


def build_qa_summary_text(analysis: dict) -> str:
    """One-paragraph QA summary for Telegram / admin logs."""
    lines = [
        f"📊 {analysis['why_generated']}",
        f"💪 {analysis['strength_assessment']}",
        f"⚖️ {analysis['risk_assessment']}",
        f"✅ Confirmed: {', '.join(analysis['confirmations_present'][:4]) or 'none'}",
        f"❌ Missing:   {', '.join(analysis['confirmations_missing'][:4]) or 'none'}",
        f"📈 Outcome:   {analysis['outcome_summary']}",
    ]
    return '\n'.join(lines)


def _guess_category(name: str) -> str:
    name_l = name.lower()
    if any(k in name_l for k in ('fvg', 'order_block', 'ob_', 'bos', 'choch', 'ote',
                                  'liquidity', 'premium', 'discount', 'breaker', 'killzone',
                                  'daily_bias', 'ict', 'sweep', 'inducement')):
        return 'ict'
    if any(k in name_l for k in ('structure', 'swing', 'higher_high', 'lower_low',
                                  'trend_line', 'support', 'resistance')):
        return 'structure'
    if any(k in name_l for k in ('trend', 'ema', 'sma', 'ma_', 'adx', 'supertrend')):
        return 'trend'
    if any(k in name_l for k in ('rsi', 'macd', 'stoch', 'cci', 'momentum', 'mfi', 'williams')):
        return 'momentum'
    if any(k in name_l for k in ('atr', 'bb', 'bollinger', 'volatility', 'vix', 'keltner')):
        return 'volatility'
    if any(k in name_l for k in ('volume', 'obv', 'vwap', 'cmf', 'delta')):
        return 'volume'
    if any(k in name_l for k in ('fib', 'fibonacci', 'retracement', 'extension')):
        return 'fibonacci'
    return 'other'


def _format_name(name: str) -> str:
    return name.replace('_', ' ').title()


def _confidence_band(c: int) -> str:
    if c >= 90: return 'ULTRA HIGH'
    if c >= 80: return 'HIGH+'
    if c >= 75: return 'HIGH'
    if c >= 65: return 'MEDIUM+'
    if c >= 55: return 'MEDIUM'
    return 'LOW'
