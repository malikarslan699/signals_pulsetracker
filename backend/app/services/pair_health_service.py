from __future__ import annotations


def classify_pair_health(
    *,
    total_closed: int,
    wins: int,
    losses: int,
    avg_pwin_tp1: float | None,
    avg_pnl: float | None,
) -> dict:
    total_closed = max(0, int(total_closed or 0))
    wins = max(0, int(wins or 0))
    losses = max(0, int(losses or 0))
    avg_pwin_tp1 = float(avg_pwin_tp1 or 0.0)
    avg_pnl = float(avg_pnl or 0.0)

    win_rate = (wins / total_closed * 100.0) if total_closed > 0 else 0.0
    sample_factor = min(1.0, total_closed / 12.0)
    quality = (win_rate * 0.55) + (avg_pwin_tp1 * 0.35) + (max(-8.0, min(8.0, avg_pnl)) * 1.25)
    health_score = max(0.0, min(100.0, quality * sample_factor))

    status = "watch"
    auto_disabled = False
    disable_reason = None

    if total_closed < 4:
        status = "watch"
    elif total_closed >= 6 and (win_rate < 35.0 or (losses >= max(4, wins * 2) and avg_pwin_tp1 < 74.0)):
        status = "disabled"
        auto_disabled = True
        disable_reason = (
            f"Auto-disabled: {wins}/{total_closed} wins, {losses} losses, "
            f"{avg_pwin_tp1:.1f}% avg calibrated TP1 win probability."
        )
    elif win_rate >= 58.0 and avg_pwin_tp1 >= 78.0:
        status = "healthy"
    elif win_rate >= 45.0 and avg_pwin_tp1 >= 70.0:
        status = "watch"
    else:
        status = "weak"

    return {
        "win_rate": round(win_rate, 1),
        "health_score": round(health_score, 2),
        "health_status": status,
        "auto_disabled": auto_disabled,
        "disable_reason": disable_reason,
    }
