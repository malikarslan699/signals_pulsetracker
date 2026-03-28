from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CalibratedSignal:
    setup_score: int
    pwin_tp1: int
    pwin_tp2: int
    ranking_score: float


class PracticalCalibrator:
    """
    Lightweight production-safe calibrator.
    Uses a monotonic ruleset so higher-quality setups always map to higher
    win probabilities without introducing opaque ML behavior.
    """

    def calibrate(
        self,
        *,
        setup_score: int,
        rr_tp1: float,
        rr_tp2: float,
        entry_type: str,
        htf_alignment_count: int,
        htf_conflict: bool,
        structure_hits: int,
        entry_hits: int,
        trend_hits: int,
    ) -> CalibratedSignal:
        score = max(0, min(100, int(round(setup_score))))

        p1 = 28 + (score * 0.48)
        p2 = 12 + (score * 0.34)

        p1 += min(8, max(0, (rr_tp1 - 1.2) * 6))
        p2 += min(10, max(0, (rr_tp2 - 1.6) * 4))

        if entry_type == "OTE_RETRACE":
            p1 += 4
            p2 += 3
        elif entry_type == "ORDER_BLOCK":
            p1 += 3
            p2 += 2
        elif entry_type == "FVG_RETEST":
            p1 += 2
            p2 += 1

        p1 += min(8, htf_alignment_count * 4)
        p2 += min(10, htf_alignment_count * 5)
        p1 += min(5, structure_hits * 2)
        p2 += min(4, entry_hits * 2)
        p1 += min(4, trend_hits)
        p2 += min(4, trend_hits)

        if htf_conflict:
            p1 -= 12
            p2 -= 15

        p1 = max(5, min(93, int(round(p1))))
        p2 = max(3, min(p1 - 2, int(round(p2))))

        ranking = (
            score * 0.55
            + p1 * 0.30
            + p2 * 0.15
            + min(6.0, max(0.0, (rr_tp2 - 1.8) * 3.0))
        )
        if htf_conflict:
            ranking -= 10.0

        return CalibratedSignal(
            setup_score=score,
            pwin_tp1=p1,
            pwin_tp2=p2,
            ranking_score=round(max(0.0, min(100.0, ranking)), 2),
        )
