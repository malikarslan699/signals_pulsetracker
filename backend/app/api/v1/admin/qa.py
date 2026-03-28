"""
QA / Research API — PulseSignal Pro Internal Testing Zone
Admin-only endpoints for signal quality analysis and auditing.
"""
from __future__ import annotations

import json
from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.auth import get_current_active_user, require_role
from app.database import get_db
from app.models.user import User
from app.services.pair_health_service import classify_pair_health
from app.services.signal_lifecycle import (
    LOSS_STATUS_SQL,
    OPEN_STATUS_SQL,
    STALE_STATUS_SQL,
    WIN_STATUS_SQL,
    canonicalize_status,
    is_loss_status,
    is_win_status,
)


def _parse_score_breakdown(value) -> dict:
    import json

    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _triggered_indicator_keys(score_breakdown: dict) -> set[str]:
    triggered: set[str] = set()
    for key, val in score_breakdown.items():
        if not isinstance(val, dict):
            continue
        if not bool(val.get("triggered")):
            continue
        try:
            score = float(val.get("score", 0) or 0)
        except Exception:
            score = 0.0
        if score > 0:
            triggered.add(str(key))
    return triggered


async def require_qa_access(current_user: User = Depends(get_current_active_user)) -> User:
    """Allow owner always; allow admin only if qa_access=True."""
    if current_user.role in ("owner", "superadmin"):
        return current_user
    if current_user.role == "admin" and getattr(current_user, "qa_access", False):
        return current_user
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail="QA Lab access not granted.")


router = APIRouter(
    prefix="/admin/qa",
    tags=["Admin — QA Research"],
    dependencies=[Depends(require_qa_access)],
)


@router.get("/signal-log", summary="Recent signals with full QA breakdown")
async def signal_log(
    limit: int = Query(default=50, ge=1, le=200),
    days: int = Query(default=7, ge=1, le=90),
    market: Optional[str] = Query(default=None),
    timeframe: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    min_confidence: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Returns recent signals with full score breakdown, MTF analysis,
    and QA reasoning for the internal testing zone.
    """
    from engine.qa_analyzer import analyze_signal
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    conditions = ["fired_at >= :cutoff", "confidence >= :min_confidence"]
    params: dict = {"cutoff": cutoff, "min_confidence": min_confidence, "limit": limit}

    if market:
        conditions.append("market = :market")
        params["market"] = market
    if timeframe:
        conditions.append("timeframe = :timeframe")
        params["timeframe"] = timeframe
    if status:
        conditions.append("status = :status")
        params["status"] = status

    where = " AND ".join(conditions)
    rows = await db.execute(text(f"""
        SELECT id, symbol, market, direction, timeframe, confidence,
               setup_score, pwin_tp1, pwin_tp2, ranking_score,
               raw_score, max_possible_score, entry, stop_loss,
               take_profit_1, take_profit_2, take_profit_3, rr_ratio,
               status, pnl_pct, fired_at, expires_at, closed_at,
               score_breakdown, mtf_analysis
        FROM signals
        WHERE {where}
        ORDER BY fired_at DESC
        LIMIT :limit
    """), params)

    signals = []
    for row in rows.mappings():
        sb = _parse_score_breakdown(row["score_breakdown"])
        mtf = row["mtf_analysis"] or {}
        if isinstance(mtf, str):
            try: mtf = json.loads(mtf)
            except: mtf = {}

        qa = analyze_signal(
            score_breakdown=sb,
            mtf_analysis=mtf,
            confidence=row["confidence"],
            direction=row["direction"],
            timeframe=row["timeframe"],
            symbol=row["symbol"],
            entry=float(row["entry"] or 0),
            stop_loss=float(row["stop_loss"] or 0),
            take_profit_1=float(row["take_profit_1"] or 0),
            take_profit_2=float(row["take_profit_2"] or 0),
            rr_ratio=float(row["rr_ratio"] or 0),
            status=row["status"],
            pnl_pct=float(row["pnl_pct"]) if row["pnl_pct"] is not None else None,
        )

        signals.append({
            "id": str(row["id"]),
            "symbol": row["symbol"],
            "market": row["market"],
            "direction": row["direction"],
            "timeframe": row["timeframe"],
            "confidence": row["confidence"],
            "setup_score": row["setup_score"],
            "pwin_tp1": float(row["pwin_tp1"]) if row["pwin_tp1"] is not None else None,
            "pwin_tp2": float(row["pwin_tp2"]) if row["pwin_tp2"] is not None else None,
            "ranking_score": float(row["ranking_score"]) if row["ranking_score"] is not None else None,
            "status": row["status"],
            "pnl_pct": float(row["pnl_pct"]) if row["pnl_pct"] is not None else None,
            "fired_at": row["fired_at"].isoformat() if row["fired_at"] else None,
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
            "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
            "entry": float(row["entry"] or 0),
            "stop_loss": float(row["stop_loss"] or 0),
            "take_profit_1": float(row["take_profit_1"] or 0),
            "rr_ratio": float(row["rr_ratio"] or 0),
            "qa": qa,
        })

    return {"signals": signals, "count": len(signals), "days": days}


@router.get("/stats", summary="Aggregate QA statistics")
async def qa_stats(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Aggregate stats: win rate by TF, market, confidence band, direction.
    Identifies noisy pairs, best-performing setups, weak patterns.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Overall counts
    overall = await db.execute(text(f"""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses,
            COUNT(*) FILTER (WHERE status IN {STALE_STATUS_SQL}) as expired,
            COUNT(*) FILTER (WHERE status IN {OPEN_STATUS_SQL}) as active,
            ROUND(AVG(confidence)::numeric, 1) as avg_confidence,
            ROUND(AVG(rr_ratio)::numeric, 2) as avg_rr
        FROM signals
        WHERE fired_at >= :cutoff
    """), {"cutoff": cutoff})
    ov = overall.mappings().first() or {}

    # By timeframe
    by_tf = await db.execute(text(f"""
        SELECT timeframe,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses,
            ROUND(AVG(confidence)::numeric,1) as avg_confidence
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY timeframe ORDER BY total DESC
    """), {"cutoff": cutoff})

    # By market
    by_market = await db.execute(text(f"""
        SELECT market,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY market
    """), {"cutoff": cutoff})

    # Noisy pairs (most signals generated)
    noisy_pairs = await db.execute(text(f"""
        SELECT symbol, COUNT(*) as signal_count,
            ROUND(AVG(confidence)::numeric,1) as avg_confidence,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY symbol ORDER BY signal_count DESC LIMIT 15
    """), {"cutoff": cutoff})

    # Confidence band distribution
    bands = await db.execute(text(f"""
        SELECT
            CASE
                WHEN confidence >= 90 THEN 'ULTRA_HIGH (90+)'
                WHEN confidence >= 80 THEN 'HIGH+ (80-89)'
                WHEN confidence >= 75 THEN 'HIGH (75-79)'
                WHEN confidence >= 65 THEN 'MEDIUM+ (65-74)'
                ELSE 'BELOW_THRESHOLD (<65)'
            END as band,
            COUNT(*) as count,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY band ORDER BY band
    """), {"cutoff": cutoff})

    # Direction breakdown
    by_dir = await db.execute(text(f"""
        SELECT direction,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses,
            ROUND(AVG(pnl_pct)::numeric, 2) as avg_pnl
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY direction
    """), {"cutoff": cutoff})

    confidence_deciles_rows = await db.execute(text(f"""
        SELECT
            CONCAT((FLOOR(confidence / 10.0) * 10)::int, '-', (FLOOR(confidence / 10.0) * 10 + 9)::int) AS decile,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) AS wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) AS losses,
            ROUND(AVG(pwin_tp1)::numeric, 1) AS avg_pwin_tp1,
            ROUND(AVG(pwin_tp2)::numeric, 1) AS avg_pwin_tp2
        FROM signals
        WHERE fired_at >= :cutoff
          AND confidence IS NOT NULL
        GROUP BY FLOOR(confidence / 10.0)
        ORDER BY FLOOR(confidence / 10.0)
    """), {"cutoff": cutoff})

    indicator_rows = await db.execute(text(f"""
        SELECT score_breakdown, status
        FROM signals
        WHERE fired_at >= :cutoff
          AND score_breakdown IS NOT NULL
          AND status NOT IN {OPEN_STATUS_SQL}
        LIMIT 500
    """), {"cutoff": cutoff})

    indicator_perf: dict[str, dict] = {}
    for row in indicator_rows.mappings():
        sb = _parse_score_breakdown(row["score_breakdown"])
        triggered = _triggered_indicator_keys(sb)
        is_win = is_win_status(row["status"])
        is_loss = is_loss_status(row["status"])
        for key in triggered:
            current = indicator_perf.setdefault(key, {"indicator": key, "count": 0, "wins": 0, "losses": 0})
            current["count"] += 1
            if is_win:
                current["wins"] += 1
            if is_loss:
                current["losses"] += 1

    indicator_performance = []
    for item in indicator_perf.values():
        wins = item["wins"]
        losses = item["losses"]
        total = item["count"]
        item["win_rate"] = win_rate(wins, losses)
        item["quality_bias"] = round(((wins - losses) / total) * 100, 1) if total else 0.0
        indicator_performance.append(item)
    indicator_performance.sort(
        key=lambda item: (
            item["win_rate"] if item["win_rate"] is not None else -1,
            item["count"],
        ),
        reverse=True,
    )

    pair_rows = await db.execute(text(f"""
        SELECT
            p.symbol,
            p.market,
            p.auto_disabled,
            p.manual_override,
            p.health_score,
            p.health_status,
            p.disable_reason,
            COUNT(s.id) FILTER (WHERE s.status NOT IN {OPEN_STATUS_SQL}) AS total_closed,
            COUNT(s.id) FILTER (WHERE s.status IN {WIN_STATUS_SQL}) AS wins,
            COUNT(s.id) FILTER (WHERE s.status IN {LOSS_STATUS_SQL}) AS losses,
            ROUND(AVG(s.pwin_tp1)::numeric, 1) AS avg_pwin_tp1,
            ROUND(AVG(s.pnl_pct)::numeric, 2) AS avg_pnl
        FROM pairs p
        LEFT JOIN signals s
          ON s.symbol = p.symbol
         AND s.fired_at >= :cutoff
        WHERE p.is_active = true
        GROUP BY p.symbol, p.market, p.auto_disabled, p.manual_override, p.health_score, p.health_status, p.disable_reason
        ORDER BY p.symbol
    """), {"cutoff": cutoff})

    def win_rate(w, l):
        return round(w / (w + l) * 100, 1) if (w + l) > 0 else None

    def to_list(rows):
        result = []
        for r in rows.mappings():
            d = dict(r)
            w = d.get('wins', 0) or 0
            l = d.get('losses', 0) or 0
            d['win_rate'] = win_rate(w, l)
            result.append(d)
        return result

    confidence_deciles = to_list(confidence_deciles_rows)

    pair_health = []
    for row in pair_rows.mappings():
        metrics = classify_pair_health(
            total_closed=int(row["total_closed"] or 0),
            wins=int(row["wins"] or 0),
            losses=int(row["losses"] or 0),
            avg_pwin_tp1=float(row["avg_pwin_tp1"] or 0),
            avg_pnl=float(row["avg_pnl"] or 0),
        )
        pair_health.append(
            {
                "symbol": row["symbol"],
                "market": row["market"],
                "total_closed": int(row["total_closed"] or 0),
                "wins": int(row["wins"] or 0),
                "losses": int(row["losses"] or 0),
                "win_rate": metrics["win_rate"],
                "avg_pwin_tp1": float(row["avg_pwin_tp1"] or 0),
                "avg_pnl": float(row["avg_pnl"] or 0),
                "health_score": float(row["health_score"] or metrics["health_score"] or 0),
                "health_status": row["health_status"] or metrics["health_status"],
                "auto_disabled": bool(row["auto_disabled"]),
                "manual_override": bool(row["manual_override"]),
                "disable_reason": row["disable_reason"] or metrics["disable_reason"],
            }
        )
    pair_health.sort(key=lambda item: (item["health_score"], item["total_closed"]), reverse=True)

    ov_dict = dict(ov) if ov else {}
    ov_w = ov_dict.get('wins', 0) or 0
    ov_l = ov_dict.get('losses', 0) or 0

    return {
        "days": days,
        "overall": {**ov_dict, "win_rate": win_rate(ov_w, ov_l)},
        "by_timeframe": to_list(by_tf),
        "by_market": to_list(by_market),
        "by_direction": to_list(by_dir),
        "noisy_pairs": to_list(noisy_pairs),
        "confidence_bands": to_list(bands),
        "confidence_deciles": confidence_deciles,
        "confidence_vs_win_rate": confidence_deciles,
        "indicator_performance": indicator_performance[:25],
        "pair_health": pair_health[:40],
    }


@router.patch("/pair-health/{symbol}/override", summary="Toggle pair manual override for auto-filtering")
async def toggle_pair_override(
    symbol: str,
    enabled: bool,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    target = symbol.upper().strip()
    await db.execute(
        text(
            """
            UPDATE pairs
            SET manual_override = :enabled
            WHERE symbol = :symbol
            """
        ),
        {"enabled": enabled, "symbol": target},
    )
    result = await db.execute(
        text(
            """
            SELECT symbol, manual_override, auto_disabled, health_status, disable_reason
            FROM pairs
            WHERE symbol = :symbol
            """
        ),
        {"symbol": target},
    )
    row = result.mappings().first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pair not found")
    return {
        "symbol": row["symbol"],
        "manual_override": bool(row["manual_override"]),
        "auto_disabled": bool(row["auto_disabled"]),
        "health_status": row["health_status"],
        "disable_reason": row["disable_reason"],
    }


@router.get("/signal/{signal_id}", summary="Deep QA breakdown for a single signal")
async def signal_qa_detail(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Full QA research record for a single signal."""
    from engine.qa_analyzer import analyze_signal, build_qa_summary_text
    row = await db.execute(text("""
        SELECT id, symbol, market, direction, timeframe, confidence,
               raw_score, max_possible_score, entry, stop_loss,
               take_profit_1, take_profit_2, take_profit_3, rr_ratio,
               status, pnl_pct, fired_at, expires_at, closed_at,
               score_breakdown, mtf_analysis, ict_zones, candle_snapshot
        FROM signals WHERE id = :id
    """), {"id": signal_id})

    sig = row.mappings().first()
    if not sig:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Signal not found")

    sb = _parse_score_breakdown(sig["score_breakdown"])
    mtf = sig["mtf_analysis"] or {}
    if isinstance(mtf, str):
        try: mtf = json.loads(mtf)
        except: mtf = {}

    qa = analyze_signal(
        score_breakdown=sb,
        mtf_analysis=mtf,
        confidence=sig["confidence"],
        direction=sig["direction"],
        timeframe=sig["timeframe"],
        symbol=sig["symbol"],
        entry=float(sig["entry"] or 0),
        stop_loss=float(sig["stop_loss"] or 0),
        take_profit_1=float(sig["take_profit_1"] or 0),
        take_profit_2=float(sig["take_profit_2"] or 0),
        rr_ratio=float(sig["rr_ratio"] or 0),
        status=sig["status"],
        pnl_pct=float(sig["pnl_pct"]) if sig["pnl_pct"] is not None else None,
    )

    return {
        "signal": {
            "id": str(sig["id"]),
            "symbol": sig["symbol"],
            "market": sig["market"],
            "direction": sig["direction"],
            "timeframe": sig["timeframe"],
            "confidence": sig["confidence"],
            "raw_score": sig["raw_score"],
            "max_possible_score": sig["max_possible_score"],
            "entry": float(sig["entry"] or 0),
            "stop_loss": float(sig["stop_loss"] or 0),
            "take_profit_1": float(sig["take_profit_1"] or 0),
            "take_profit_2": float(sig["take_profit_2"] or 0),
            "take_profit_3": float(sig["take_profit_3"] or 0),
            "rr_ratio": float(sig["rr_ratio"] or 0),
            "status": sig["status"],
            "pnl_pct": float(sig["pnl_pct"]) if sig["pnl_pct"] is not None else None,
            "fired_at": sig["fired_at"].isoformat() if sig["fired_at"] else None,
            "expires_at": sig["expires_at"].isoformat() if sig["expires_at"] else None,
            "closed_at": sig["closed_at"].isoformat() if sig["closed_at"] else None,
            "score_breakdown": sb,
            "mtf_analysis": mtf,
        },
        "qa": qa,
        "summary_text": build_qa_summary_text(qa),
    }


@router.get("/false-positives", summary="Signals that expired or hit SL quickly")
async def false_positives(
    days: int = Query(default=7),
    max_hours_to_close: float = Query(default=2.0, description="Signals closed within N hours"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Identify fast failures — signals that hit SL or expired within a short window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = await db.execute(text(f"""
        SELECT symbol, market, direction, timeframe, confidence, status,
               pnl_pct, fired_at, closed_at,
               EXTRACT(EPOCH FROM (closed_at - fired_at))/3600 as hours_to_close
        FROM signals
        WHERE fired_at >= :cutoff
          AND (status IN {LOSS_STATUS_SQL} OR status IN {STALE_STATUS_SQL})
          AND closed_at IS NOT NULL
          AND EXTRACT(EPOCH FROM (closed_at - fired_at))/3600 <= :max_hours
        ORDER BY hours_to_close ASC
        LIMIT 100
    """), {"cutoff": cutoff, "max_hours": max_hours_to_close})

    results = [dict(r) for r in rows.mappings()]
    for r in results:
        if r.get('fired_at'): r['fired_at'] = r['fired_at'].isoformat()
        if r.get('closed_at'): r['closed_at'] = r['closed_at'].isoformat()

    return {"false_positives": results, "count": len(results)}


@router.get("/indicator-performance", summary="Which indicators correlate with wins")
async def indicator_performance(
    days: int = Query(default=14),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Aggregates top_confluences field to find which indicator combinations
    appear most often in winning vs losing signals.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # We count signal outcomes grouped by confidence band and timeframe
    # as a proxy for indicator performance (score_breakdown parsing is done in Python)
    rows = await db.execute(text(f"""
        SELECT
            timeframe,
            CASE WHEN confidence >= 85 THEN 'HIGH' ELSE 'MEDIUM' END as conf_band,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as wins,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as losses,
            ROUND(AVG(confidence)::numeric, 1) as avg_confidence,
            ROUND(AVG(CASE WHEN status IN {WIN_STATUS_SQL} THEN pnl_pct END)::numeric, 2) as avg_win_pnl,
            ROUND(AVG(CASE WHEN status IN {LOSS_STATUS_SQL} THEN pnl_pct END)::numeric, 2) as avg_loss_pnl
        FROM signals
        WHERE fired_at >= :cutoff
          AND status NOT IN {OPEN_STATUS_SQL}
        GROUP BY timeframe, conf_band
        ORDER BY timeframe, conf_band
    """), {"cutoff": cutoff})

    results = [dict(r) for r in rows.mappings()]
    for r in results:
        w = r.get('wins', 0) or 0
        l = r.get('losses', 0) or 0
        r['win_rate'] = round(w / (w + l) * 100, 1) if (w + l) > 0 else None

    return {"performance": results, "days": days}


@router.get("/failure-analysis", summary="Why are signals failing? Indicator-level breakdown of SL hits")
async def failure_analysis(
    days: int = Query(default=14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Deep dive into losing trades:
    - Which pairs have the worst SL hit rate
    - Which timeframes produce most losses
    - Average time before SL hit
    - R:R distribution for losses vs wins
    - Confidence at time of loss (were we overconfident?)
    - Direction bias in failures (more LONGs fail or SHORTs?)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # SL hit stats by pair
    sl_by_pair = await db.execute(text(f"""
        SELECT symbol, market, direction,
            COUNT(*) as sl_count,
            ROUND(AVG(confidence)::numeric, 1) as avg_confidence_at_loss,
            ROUND(AVG(rr_ratio)::numeric, 2) as avg_rr,
            ROUND(AVG(EXTRACT(EPOCH FROM (closed_at - fired_at))/3600)::numeric, 1) as avg_hours_to_sl,
            MIN(EXTRACT(EPOCH FROM (closed_at - fired_at))/60)::int as fastest_sl_min
        FROM signals
        WHERE fired_at >= :cutoff
          AND status IN {LOSS_STATUS_SQL}
          AND closed_at IS NOT NULL
        GROUP BY symbol, market, direction
        ORDER BY sl_count DESC
        LIMIT 20
    """), {"cutoff": cutoff})

    # SL hit stats by timeframe
    sl_by_tf = await db.execute(text(f"""
        SELECT timeframe,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as sl_hits,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as tp_hits,
            ROUND(AVG(confidence) FILTER (WHERE status IN {LOSS_STATUS_SQL})::numeric, 1) as avg_conf_loss,
            ROUND(AVG(confidence) FILTER (WHERE status IN {WIN_STATUS_SQL})::numeric, 1) as avg_conf_win,
            ROUND(AVG(rr_ratio) FILTER (WHERE status IN {LOSS_STATUS_SQL})::numeric, 2) as avg_rr_loss,
            ROUND(AVG(rr_ratio) FILTER (WHERE status IN {WIN_STATUS_SQL})::numeric, 2) as avg_rr_win
        FROM signals
        WHERE fired_at >= :cutoff AND status NOT IN {OPEN_STATUS_SQL}
        GROUP BY timeframe
        ORDER BY sl_hits DESC
    """), {"cutoff": cutoff})

    # Overconfidence check: signals with high confidence that still hit SL
    overconfident_losses = await db.execute(text(f"""
        SELECT symbol, direction, timeframe, confidence, rr_ratio, pnl_pct,
               fired_at, closed_at,
               EXTRACT(EPOCH FROM (closed_at - fired_at))/3600 as hours_held
        FROM signals
        WHERE fired_at >= :cutoff
          AND status IN {LOSS_STATUS_SQL}
          AND confidence >= 85
          AND closed_at IS NOT NULL
        ORDER BY confidence DESC
        LIMIT 20
    """), {"cutoff": cutoff})

    # Direction failure bias
    dir_bias = await db.execute(text(f"""
        SELECT direction,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN {LOSS_STATUS_SQL}) as sl_hits,
            COUNT(*) FILTER (WHERE status IN {WIN_STATUS_SQL}) as tp_hits,
            ROUND(AVG(confidence)::numeric, 1) as avg_confidence
        FROM signals
        WHERE fired_at >= :cutoff AND (status IN {LOSS_STATUS_SQL} OR status IN {WIN_STATUS_SQL})
        GROUP BY direction
    """), {"cutoff": cutoff})

    # Signals with score_breakdown — extract which indicators were present in losses
    sl_signals_raw = await db.execute(text(f"""
        SELECT score_breakdown
        FROM signals
        WHERE fired_at >= :cutoff
          AND status IN {LOSS_STATUS_SQL}
          AND score_breakdown IS NOT NULL
        LIMIT 100
    """), {"cutoff": cutoff})

    tp_signals_raw = await db.execute(text(f"""
        SELECT score_breakdown
        FROM signals
        WHERE fired_at >= :cutoff
          AND status IN {WIN_STATUS_SQL}
          AND score_breakdown IS NOT NULL
        LIMIT 100
    """), {"cutoff": cutoff})

    # Tally which indicator keys appeared in wins vs losses
    sl_indicator_counts: dict = {}
    tp_indicator_counts: dict = {}

    def tally_indicators(rows, counter):
        total_rows = 0
        for row in rows.mappings():
            sb = _parse_score_breakdown(row["score_breakdown"])
            triggered = _triggered_indicator_keys(sb)
            if not triggered:
                continue
            total_rows += 1
            for key in triggered:
                counter[key] = counter.get(key, 0) + 1
        return total_rows

    sl_total_rows = tally_indicators(sl_signals_raw, sl_indicator_counts)
    tp_total_rows = tally_indicators(tp_signals_raw, tp_indicator_counts)

    # Build indicator comparison: appears more in losses = potentially noisy
    all_indicators = set(sl_indicator_counts) | set(tp_indicator_counts)
    sl_total = sl_total_rows or 1
    tp_total = tp_total_rows or 1

    indicator_comparison = []
    for ind in sorted(all_indicators):
        sl_pct = round(sl_indicator_counts.get(ind, 0) / sl_total * 100, 1)
        tp_pct = round(tp_indicator_counts.get(ind, 0) / tp_total * 100, 1)
        noise_score = round(sl_pct - tp_pct, 1)  # positive = noisy (more in losses)
        indicator_comparison.append({
            "indicator": ind,
            "in_losses_pct": sl_pct,
            "in_wins_pct": tp_pct,
            "noise_score": noise_score,
            "assessment": "noisy" if noise_score > 5 else "reliable" if noise_score < -5 else "neutral",
        })
    indicator_comparison.sort(key=lambda x: x["noise_score"], reverse=True)

    def serialize(rows):
        result = []
        for r in rows.mappings():
            d = dict(r)
            if d.get("fired_at"): d["fired_at"] = d["fired_at"].isoformat()
            if d.get("closed_at"): d["closed_at"] = d["closed_at"].isoformat()
            result.append(d)
        return result

    def with_wr(rows):
        result = serialize(rows)
        for r in result:
            w = r.get("tp_hits", 0) or 0
            l = r.get("sl_hits", 0) or 0
            r["win_rate"] = round(w / (w + l) * 100, 1) if (w + l) > 0 else None
        return result

    return {
        "days": days,
        "sl_by_pair": serialize(sl_by_pair),
        "sl_by_timeframe": with_wr(sl_by_tf),
        "overconfident_losses": serialize(overconfident_losses),
        "direction_bias": with_wr(dir_bias),
        "indicator_noise_analysis": indicator_comparison,
        "summary": {
            "noisy_indicators": [x["indicator"] for x in indicator_comparison if x["assessment"] == "noisy"][:5],
            "reliable_indicators": [x["indicator"] for x in indicator_comparison if x["assessment"] == "reliable"][:5],
        },
    }
