"""
QA / Research API — PulseSignal Pro Internal Testing Zone
Admin-only endpoints for signal quality analysis and auditing.
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.auth import get_current_active_user, require_role
from app.database import get_db
from app.models.user import User

router = APIRouter(
    prefix="/admin/qa",
    tags=["Admin — QA Research"],
    dependencies=[Depends(require_role("admin", "owner"))],
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
    import json

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
        sb = row["score_breakdown"] or {}
        mtf = row["mtf_analysis"] or {}
        if isinstance(sb, str):
            try: sb = json.loads(sb)
            except: sb = {}
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
    overall = await db.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses,
            COUNT(*) FILTER (WHERE status = 'expired') as expired,
            COUNT(*) FILTER (WHERE status = 'active') as active,
            ROUND(AVG(confidence)::numeric, 1) as avg_confidence,
            ROUND(AVG(rr_ratio)::numeric, 2) as avg_rr
        FROM signals
        WHERE fired_at >= :cutoff
    """), {"cutoff": cutoff})
    ov = overall.mappings().first() or {}

    # By timeframe
    by_tf = await db.execute(text("""
        SELECT timeframe,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses,
            ROUND(AVG(confidence)::numeric,1) as avg_confidence
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY timeframe ORDER BY total DESC
    """), {"cutoff": cutoff})

    # By market
    by_market = await db.execute(text("""
        SELECT market,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY market
    """), {"cutoff": cutoff})

    # Noisy pairs (most signals generated)
    noisy_pairs = await db.execute(text("""
        SELECT symbol, COUNT(*) as signal_count,
            ROUND(AVG(confidence)::numeric,1) as avg_confidence,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY symbol ORDER BY signal_count DESC LIMIT 15
    """), {"cutoff": cutoff})

    # Confidence band distribution
    bands = await db.execute(text("""
        SELECT
            CASE
                WHEN confidence >= 90 THEN 'ULTRA_HIGH (90+)'
                WHEN confidence >= 80 THEN 'HIGH+ (80-89)'
                WHEN confidence >= 75 THEN 'HIGH (75-79)'
                WHEN confidence >= 65 THEN 'MEDIUM+ (65-74)'
                ELSE 'BELOW_THRESHOLD (<65)'
            END as band,
            COUNT(*) as count,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY band ORDER BY band
    """), {"cutoff": cutoff})

    # Direction breakdown
    by_dir = await db.execute(text("""
        SELECT direction,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses,
            ROUND(AVG(pnl_pct)::numeric, 2) as avg_pnl
        FROM signals WHERE fired_at >= :cutoff
        GROUP BY direction
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
    }


@router.get("/signal/{signal_id}", summary="Deep QA breakdown for a single signal")
async def signal_qa_detail(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Full QA research record for a single signal."""
    from engine.qa_analyzer import analyze_signal, build_qa_summary_text
    import json

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

    sb = sig["score_breakdown"] or {}
    mtf = sig["mtf_analysis"] or {}
    if isinstance(sb, str):
        try: sb = json.loads(sb)
        except: sb = {}
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

    rows = await db.execute(text("""
        SELECT symbol, market, direction, timeframe, confidence, status,
               pnl_pct, fired_at, closed_at,
               EXTRACT(EPOCH FROM (closed_at - fired_at))/3600 as hours_to_close
        FROM signals
        WHERE fired_at >= :cutoff
          AND status IN ('sl_hit', 'expired')
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
    rows = await db.execute(text("""
        SELECT
            timeframe,
            CASE WHEN confidence >= 85 THEN 'HIGH' ELSE 'MEDIUM' END as conf_band,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status IN ('tp1_hit','tp2_hit','tp3_hit')) as wins,
            COUNT(*) FILTER (WHERE status = 'sl_hit') as losses,
            ROUND(AVG(confidence)::numeric, 1) as avg_confidence,
            ROUND(AVG(CASE WHEN status IN ('tp1_hit','tp2_hit','tp3_hit') THEN pnl_pct END)::numeric, 2) as avg_win_pnl,
            ROUND(AVG(CASE WHEN status = 'sl_hit' THEN pnl_pct END)::numeric, 2) as avg_loss_pnl
        FROM signals
        WHERE fired_at >= :cutoff
          AND status != 'active'
        GROUP BY timeframe, conf_band
        ORDER BY timeframe, conf_band
    """), {"cutoff": cutoff})

    results = [dict(r) for r in rows.mappings()]
    for r in results:
        w = r.get('wins', 0) or 0
        l = r.get('losses', 0) or 0
        r['win_rate'] = round(w / (w + l) * 100, 1) if (w + l) > 0 else None

    return {"performance": results, "days": days}
