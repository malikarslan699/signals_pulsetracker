"""
PulseSignal Pro — Signal Generator

Phase 2 trading-engine planner.
Builds only tradable setups through a hard gating funnel:
HTF trend -> structure -> entry zone -> risk/targets -> signal creation.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

from .calibration import PracticalCalibrator
from .candle_utils import Candle
from .scoring.normalizer import score_to_confidence_band
from .scoring.scorer import MasterScorer, SignalScore


@dataclass
class GeneratedSignal:
    id: str
    symbol: str
    market: str
    direction: str
    timeframe: str

    confidence: int
    setup_score: int
    pwin_tp1: int
    pwin_tp2: int
    ranking_score: float
    confidence_band: str
    raw_score: int
    max_possible_score: int

    entry: float
    entry_zone_low: float
    entry_zone_high: float
    entry_type: str
    stop_loss: float
    invalidation_price: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    rr_ratio: float
    rr_tp1: float
    rr_tp2: float

    status: str
    score_breakdown: dict
    ict_zones: dict
    mtf_analysis: dict
    candle_snapshot: dict
    top_confluences: list[str]

    fired_at: str
    valid_until: str
    expires_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    def summary_line(self) -> str:
        return (
            f"{self.direction} {self.symbol} {self.timeframe} "
            f"({self.confidence}%) entry {self.entry:.5g} "
            f"zone {self.entry_zone_low:.5g}-{self.entry_zone_high:.5g} "
            f"TP1 {self.take_profit_1:.5g} TP2 {self.take_profit_2:.5g}"
        )


class SignalGenerator:
    MIN_CONFIDENCE: int = 75
    MIN_DIRECTION_GAP: int = 12

    TF_WEIGHTS: dict[str, float] = {
        "15m": 1.0,
        "1H": 1.25,
        "4H": 1.5,
        "1D": 2.0,
    }

    TF_EXPIRY_HOURS: dict[str, int] = {
        "15m": 6,
        "1H": 24,
        "4H": 96,
        "1D": 240,
    }

    TF_VALID_HOURS: dict[str, int] = {
        "15m": 2,
        "1H": 8,
        "4H": 30,
        "1D": 72,
    }

    def __init__(self) -> None:
        self.scorer = MasterScorer()
        self.calibrator = PracticalCalibrator()

    def generate(
        self,
        symbol: str,
        market: str,
        candles: list[Candle],
        timeframe: str,
        candles_by_tf: Optional[dict[str, list[Candle]]] = None,
    ) -> Optional[GeneratedSignal]:
        if len(candles) < 50:
            return None

        opens = np.array([c["open"] for c in candles], dtype=np.float64)
        highs = np.array([c["high"] for c in candles], dtype=np.float64)
        lows = np.array([c["low"] for c in candles], dtype=np.float64)
        closes = np.array([c["close"] for c in candles], dtype=np.float64)
        volumes = np.array([c["volume"] for c in candles], dtype=np.float64)
        timestamps = np.array([c["timestamp"] for c in candles], dtype=np.float64)

        try:
            long_score, short_score = self.scorer.score(
                opens, highs, lows, closes, volumes, timestamps, timeframe, symbol
            )
        except Exception:
            return None

        winner = self._select_candidate(long_score, short_score)
        if winner is None:
            return None

        htf_context, exported_mtf = self._build_htf_context(symbol, timeframe, candles_by_tf or {})
        for tf, data in exported_mtf.items():
            data["aligned"] = data.get("direction") == winner.direction
        if not self._passes_htf_gate(timeframe, winner.direction, htf_context):
            return None

        if not self._passes_structure_gate(winner):
            return None

        entry_plan = self._build_entry_plan(winner, closes, timeframe)
        if entry_plan is None:
            return None

        risk_plan = self._build_risk_plan(
            direction=winner.direction,
            entry_plan=entry_plan,
            closes=closes,
            highs=highs,
            lows=lows,
            primary_zones=winner.ict_zones,
            htf_context=htf_context,
        )
        if risk_plan is None:
            return None

        rr_tp1 = self._calc_rr(risk_plan["entry"], risk_plan["stop_loss"], risk_plan["take_profit_1"])
        rr_tp2 = self._calc_rr(risk_plan["entry"], risk_plan["stop_loss"], risk_plan["take_profit_2"])
        if rr_tp1 is None or rr_tp2 is None or rr_tp1 < 1.3 or rr_tp2 < 2.0:
            return None

        setup_score = self._compute_clean_confidence(winner, htf_context, entry_plan["entry_type"])
        calibrated = self._calibrate_signal(
            winner=winner,
            setup_score=setup_score,
            rr_tp1=rr_tp1,
            rr_tp2=rr_tp2,
            entry_type=entry_plan["entry_type"],
            htf_context=htf_context,
        )
        confidence = calibrated.pwin_tp1
        if confidence < max(75, self.MIN_CONFIDENCE):
            return None

        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(hours=self.TF_VALID_HOURS.get(timeframe, 8))
        expires_at = now + timedelta(hours=self.TF_EXPIRY_HOURS.get(timeframe, 24))
        current_price = float(closes[-1])
        status = self._initial_status(current_price, entry_plan["zone_low"], entry_plan["zone_high"])

        top_confluences = self._top_real_confluences(winner)
        snapshot = self._build_snapshot(candles, timeframe)

        return GeneratedSignal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            market=market,
            direction=winner.direction,
            timeframe=timeframe,
            confidence=confidence,
            setup_score=calibrated.setup_score,
            pwin_tp1=calibrated.pwin_tp1,
            pwin_tp2=calibrated.pwin_tp2,
            ranking_score=calibrated.ranking_score,
            confidence_band=score_to_confidence_band(confidence),
            raw_score=calibrated.setup_score,
            max_possible_score=100,
            entry=round(risk_plan["entry"], 8),
            entry_zone_low=round(entry_plan["zone_low"], 8),
            entry_zone_high=round(entry_plan["zone_high"], 8),
            entry_type=entry_plan["entry_type"],
            stop_loss=round(risk_plan["stop_loss"], 8),
            invalidation_price=round(risk_plan["invalidation_price"], 8),
            take_profit_1=round(risk_plan["take_profit_1"], 8),
            take_profit_2=round(risk_plan["take_profit_2"], 8),
            take_profit_3=round(risk_plan["take_profit_3"], 8),
            rr_ratio=round(rr_tp2, 2),
            rr_tp1=round(rr_tp1, 2),
            rr_tp2=round(rr_tp2, 2),
            status=status,
            score_breakdown=winner.to_breakdown_dict(),
            ict_zones=winner.ict_zones,
            mtf_analysis=exported_mtf,
            candle_snapshot=snapshot,
            top_confluences=top_confluences,
            fired_at=now.isoformat(),
            valid_until=valid_until.isoformat(),
            expires_at=expires_at.isoformat(),
        )

    def generate_multi_timeframe(
        self,
        symbol: str,
        market: str,
        candles_by_tf: dict[str, list[Candle]],
        primary_tf: str = "1H",
    ) -> list[GeneratedSignal]:
        raw_signals: list[GeneratedSignal] = []
        for tf, candles in candles_by_tf.items():
            context = {k: v for k, v in candles_by_tf.items() if k != tf}
            signal = self.generate(
                symbol=symbol,
                market=market,
                candles=candles,
                timeframe=tf,
                candles_by_tf=context,
            )
            if signal:
                raw_signals.append(signal)

        if not raw_signals:
            return []

        best_by_direction: dict[str, GeneratedSignal] = {}
        for sig in sorted(
            raw_signals,
            key=lambda s: (s.ranking_score, s.pwin_tp1, s.setup_score),
            reverse=True,
        ):
            if sig.direction not in best_by_direction:
                best_by_direction[sig.direction] = sig

        deduped = list(best_by_direction.values())
        deduped.sort(
            key=lambda s: (
                -float(s.ranking_score),
                -self.TF_WEIGHTS.get(s.timeframe, 1.0),
                -s.pwin_tp1,
            )
        )
        return deduped

    def get_best_signal(
        self,
        symbol: str,
        market: str,
        candles_by_tf: dict[str, list[Candle]],
    ) -> Optional[GeneratedSignal]:
        signals = self.generate_multi_timeframe(symbol, market, candles_by_tf)
        if not signals:
            return None
        return max(signals, key=lambda s: (s.ranking_score, s.pwin_tp1, s.setup_score))

    def batch_generate(self, requests: list[dict]) -> list[Optional[GeneratedSignal]]:
        results: list[Optional[GeneratedSignal]] = []
        for req in requests:
            try:
                sig = self.generate(
                    symbol=req["symbol"],
                    market=req["market"],
                    candles=req["candles"],
                    timeframe=req["timeframe"],
                    candles_by_tf=req.get("candles_by_tf"),
                )
            except Exception:
                sig = None
            results.append(sig)
        return results

    @staticmethod
    def filter_by_band(signals: list[GeneratedSignal], min_band: str = "MEDIUM") -> list[GeneratedSignal]:
        band_rank = {"NO_SIGNAL": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "ULTRA_HIGH": 4}
        min_rank = band_rank.get(min_band, 0)
        return [s for s in signals if band_rank.get(s.confidence_band, 0) >= min_rank]

    @staticmethod
    def format_telegram_message(signal: GeneratedSignal) -> str:
        lines = [
            f"{'🟢' if signal.direction == 'LONG' else '🔴'} *{signal.symbol}* — {signal.direction}",
            f"📊 TF: `{signal.timeframe}` | P(TP1): *{signal.pwin_tp1}%* | P(TP2): *{signal.pwin_tp2}%*",
            f"🧠 Setup Score: *{signal.setup_score}/100* | Rank: *{signal.ranking_score:.1f}*",
            f"🎯 Entry Zone: `{signal.entry_zone_low:.5g}` - `{signal.entry_zone_high:.5g}` ({signal.entry_type})",
            f"🧭 Planned Entry: `{signal.entry:.5g}`",
            f"⛔ Invalidates: `{signal.invalidation_price:.5g}` | Stop: `{signal.stop_loss:.5g}`",
            f"✅ TP1: `{signal.take_profit_1:.5g}` | RR1: `1:{signal.rr_tp1:.2f}`",
            f"🚀 TP2: `{signal.take_profit_2:.5g}` | RR2: `1:{signal.rr_tp2:.2f}`",
            f"⏳ Valid Until: `{signal.valid_until[:19]} UTC`",
            f"⌛ Expires: `{signal.expires_at[:19]} UTC`",
        ]
        if signal.top_confluences:
            lines.append("")
            lines.append("🔑 Confluences:")
            for item in signal.top_confluences[:6]:
                lines.append(f"  • {item}")
        return "\n".join(lines)

    def _select_candidate(self, long_score: SignalScore, short_score: SignalScore) -> Optional[SignalScore]:
        long_c = int(long_score.confidence or 0)
        short_c = int(short_score.confidence or 0)
        best = max(long_c, short_c)
        if best < max(60, self.MIN_CONFIDENCE - 10):
            return None
        if abs(long_c - short_c) < self.MIN_DIRECTION_GAP:
            return None
        return long_score if long_c > short_c else short_score

    def _build_htf_context(
        self,
        symbol: str,
        timeframe: str,
        candles_by_tf: dict[str, list[Candle]],
    ) -> tuple[dict[str, dict], dict[str, dict]]:
        internal: dict[str, dict] = {}
        exported: dict[str, dict] = {}
        for tf in ("1H", "4H"):
            tf_candles = candles_by_tf.get(tf)
            if tf == timeframe or not tf_candles or len(tf_candles) < 50:
                continue
            try:
                opens = np.array([c["open"] for c in tf_candles], dtype=np.float64)
                highs = np.array([c["high"] for c in tf_candles], dtype=np.float64)
                lows = np.array([c["low"] for c in tf_candles], dtype=np.float64)
                closes = np.array([c["close"] for c in tf_candles], dtype=np.float64)
                volumes = np.array([c["volume"] for c in tf_candles], dtype=np.float64)
                timestamps = np.array([c["timestamp"] for c in tf_candles], dtype=np.float64)
                long_score, short_score = self.scorer.score(opens, highs, lows, closes, volumes, timestamps, tf, symbol)
                direction = "LONG" if long_score.confidence >= short_score.confidence else "SHORT"
                gap = abs(int(long_score.confidence or 0) - int(short_score.confidence or 0))
                score_obj = long_score if direction == "LONG" else short_score
                internal[tf] = {
                    "direction": direction,
                    "gap": gap,
                    "confidence": int(score_obj.confidence or 0),
                    "score": score_obj,
                }
                exported[tf] = {
                    "long_confidence": int(long_score.confidence or 0),
                    "short_confidence": int(short_score.confidence or 0),
                    "direction": direction,
                    "aligned": False,
                    "weight": self.TF_WEIGHTS.get(tf, 1.0),
                }
            except Exception:
                continue
        return internal, exported

    def _passes_htf_gate(self, timeframe: str, direction: str, htf_context: dict[str, dict]) -> bool:
        one_h = htf_context.get("1H")
        four_h = htf_context.get("4H")

        if timeframe == "15m":
            if not one_h or one_h["direction"] != direction:
                return False
            if not four_h or four_h["direction"] != direction:
                return False
            return True

        if timeframe == "1H":
            if four_h and four_h["direction"] != direction and four_h["gap"] >= 8:
                return False
            return True

        if timeframe == "4H":
            return True

        return True

    def _passes_structure_gate(self, winner: SignalScore) -> bool:
        structure_hits = [s for s in winner.structure_scores if s.triggered and s.score > 0]
        trend_hits = [s for s in winner.trend_scores if s.triggered and s.score > 0]
        entry_hits = [
            s for s in winner.ict_scores
            if s.triggered and s.score > 0 and s.name in {
                "ICT Order Block",
                "ICT Fair Value Gap",
                "ICT OTE Zone",
                "ICT Breaker Block",
                "ICT Premium/Discount",
            }
        ]
        return bool(trend_hits) and bool(structure_hits) and bool(entry_hits)

    def _build_entry_plan(self, winner: SignalScore, closes: np.ndarray, timeframe: str) -> Optional[dict]:
        direction_key = "bullish" if winner.direction == "LONG" else "bearish"
        zones: list[dict] = []
        current_price = float(closes[-1])

        ob_group = (winner.ict_zones.get("order_blocks") or {}).get(direction_key, [])
        for item in ob_group[:5]:
            low = float(min(item.get("low", 0), item.get("high", 0)))
            high = float(max(item.get("low", 0), item.get("high", 0)))
            if low > 0 and high > low:
                zones.append({"zone_low": low, "zone_high": high, "entry_type": "ORDER_BLOCK", "priority": 1})

        fvg_group = (winner.ict_zones.get("fvg") or {}).get(direction_key, [])
        for item in fvg_group[:5]:
            low = float(min(item.get("bottom", 0), item.get("top", 0)))
            high = float(max(item.get("bottom", 0), item.get("top", 0)))
            if low > 0 and high > low:
                zones.append({"zone_low": low, "zone_high": high, "entry_type": "FVG_RETEST", "priority": 2})

        ote = winner.ict_zones.get("ote") or {}
        if ote.get("active") and ote.get("direction") == direction_key:
            low = float(min(ote.get("low", 0) or 0, ote.get("high", 0) or 0))
            high = float(max(ote.get("low", 0) or 0, ote.get("high", 0) or 0))
            if low > 0 and high > low:
                zones.append({"zone_low": low, "zone_high": high, "entry_type": "OTE_RETRACE", "priority": 0})

        if not zones:
            return None

        def zone_rank(item: dict) -> tuple[float, int, float]:
            low = item["zone_low"]
            high = item["zone_high"]
            inside = 0 if low <= current_price <= high else 1
            distance = abs(((low + high) / 2.0) - current_price)
            return (inside, int(item["priority"]), distance)

        zone = sorted(zones, key=zone_rank)[0]
        zone_low = float(zone["zone_low"])
        zone_high = float(zone["zone_high"])
        width = max(zone_high - zone_low, current_price * 0.0008)
        if width <= 0:
            return None

        if winner.direction == "LONG":
            entry = zone_low + width * 0.55
        else:
            entry = zone_high - width * 0.55

        return {
            "zone_low": zone_low,
            "zone_high": zone_high,
            "entry": entry,
            "entry_type": zone["entry_type"],
            "zone_width": width,
        }

    def _build_risk_plan(
        self,
        direction: str,
        entry_plan: dict,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        primary_zones: dict,
        htf_context: dict[str, dict],
    ) -> Optional[dict]:
        entry = float(entry_plan["entry"])
        atr_info = self.scorer._atr_analysis(highs, lows, closes, entry, direction)
        atr_val = float(atr_info.get("atr") or 0.0)
        if atr_val <= 0:
            return None

        buffer = max(atr_val * 0.35, entry * 0.0015)
        if direction == "LONG":
            invalidation = float(entry_plan["zone_low"])
            stop_loss = invalidation - buffer
        else:
            invalidation = float(entry_plan["zone_high"])
            stop_loss = invalidation + buffer

        if abs(entry - stop_loss) <= 0:
            return None

        tp1 = self._nearest_liquidity_target(direction, entry, primary_zones, htf_context, higher_timeframe=False)
        tp2 = self._nearest_liquidity_target(direction, entry, primary_zones, htf_context, higher_timeframe=True)

        risk = abs(entry - stop_loss)
        if tp1 is None:
            tp1 = entry + (risk * 2.2 if direction == "LONG" else -risk * 2.2)
        if tp2 is None:
            tp2 = entry + (risk * 3.6 if direction == "LONG" else -risk * 3.6)

        if direction == "LONG":
            if tp1 <= entry:
                tp1 = entry + risk * 2.0
            if tp2 <= tp1:
                tp2 = tp1 + risk * 1.2
            tp3 = tp2 + risk * 1.0
        else:
            if tp1 >= entry:
                tp1 = entry - risk * 2.0
            if tp2 >= tp1:
                tp2 = tp1 - risk * 1.2
            tp3 = tp2 - risk * 1.0

        return {
            "entry": entry,
            "stop_loss": stop_loss,
            "invalidation_price": invalidation,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "take_profit_3": tp3,
        }

    def _nearest_liquidity_target(
        self,
        direction: str,
        entry: float,
        primary_zones: dict,
        htf_context: dict[str, dict],
        higher_timeframe: bool,
    ) -> Optional[float]:
        sources: list[dict] = []
        if not higher_timeframe:
            sources.append(primary_zones)
        else:
            if "4H" in htf_context:
                sources.append(htf_context["4H"]["score"].ict_zones)
            sources.append(primary_zones)

        levels: list[float] = []
        for source in sources:
            liq = source.get("liquidity") or {}
            if direction == "LONG":
                for key in ("bsl",):
                    for value in liq.get(key, []) or []:
                        try:
                            price = float(value)
                        except Exception:
                            continue
                        if price > entry:
                            levels.append(price)
                for item in liq.get("equal_highs", []) or []:
                    try:
                        price = float(item.get("price", 0) or 0)
                    except Exception:
                        continue
                    if price > entry:
                        levels.append(price)
                for key in ("pdh",):
                    try:
                        price = float(liq.get(key, 0) or 0)
                    except Exception:
                        continue
                    if price > entry:
                        levels.append(price)
            else:
                for key in ("ssl",):
                    for value in liq.get(key, []) or []:
                        try:
                            price = float(value)
                        except Exception:
                            continue
                        if 0 < price < entry:
                            levels.append(price)
                for item in liq.get("equal_lows", []) or []:
                    try:
                        price = float(item.get("price", 0) or 0)
                    except Exception:
                        continue
                    if 0 < price < entry:
                        levels.append(price)
                for key in ("pdl",):
                    try:
                        price = float(liq.get(key, 0) or 0)
                    except Exception:
                        continue
                    if 0 < price < entry:
                        levels.append(price)

        if not levels:
            return None
        levels = sorted(set(round(v, 8) for v in levels))
        return levels[-1] if higher_timeframe and direction == "LONG" else (
            levels[0] if not higher_timeframe and direction == "LONG" else (
                levels[0] if higher_timeframe and direction == "SHORT" else levels[-1]
            )
        )

    def _compute_clean_confidence(self, winner: SignalScore, htf_context: dict[str, dict], entry_type: str) -> int:
        def capped_sum(items: list, cap: int) -> int:
            total = sum(int(s.score) for s in items if s.triggered and int(s.score) > 0)
            return min(cap, total)

        score = 0
        score += capped_sum(winner.trend_scores, 24)
        score += capped_sum(winner.structure_scores, 22)
        score += capped_sum(winner.ict_scores, 28)
        score += capped_sum(winner.momentum_scores, 8)
        score += capped_sum(winner.volume_scores, 8)
        score += capped_sum(winner.volatility_scores, 6)
        score += min(4, capped_sum(winner.fibonacci_scores, 4))

        if entry_type == "OTE_RETRACE":
            score += 4
        elif entry_type == "ORDER_BLOCK":
            score += 3
        elif entry_type == "FVG_RETEST":
            score += 2

        one_h = htf_context.get("1H")
        four_h = htf_context.get("4H")
        if one_h and one_h["direction"] == winner.direction:
            score += 8
        if four_h and four_h["direction"] == winner.direction:
            score += 10
        if four_h and four_h["direction"] != winner.direction and four_h["gap"] >= 8:
            score -= 12

        return max(0, min(100, int(round(score))))

    def _calibrate_signal(
        self,
        winner: SignalScore,
        setup_score: int,
        rr_tp1: float,
        rr_tp2: float,
        entry_type: str,
        htf_context: dict[str, dict],
    ):
        structure_hits = len([s for s in winner.structure_scores if s.triggered and s.score > 0])
        entry_hits = len(
            [
                s
                for s in winner.ict_scores
                if s.triggered and s.score > 0 and s.name in {
                    "ICT Order Block",
                    "ICT Fair Value Gap",
                    "ICT OTE Zone",
                    "ICT Breaker Block",
                    "ICT Premium/Discount",
                }
            ]
        )
        trend_hits = len([s for s in winner.trend_scores if s.triggered and s.score > 0])
        htf_alignment_count = sum(
            1
            for tf in ("1H", "4H")
            if htf_context.get(tf) and htf_context[tf]["direction"] == winner.direction
        )
        htf_conflict = any(
            htf_context.get(tf)
            and htf_context[tf]["direction"] != winner.direction
            and htf_context[tf]["gap"] >= 8
            for tf in ("1H", "4H")
        )
        return self.calibrator.calibrate(
            setup_score=setup_score,
            rr_tp1=float(rr_tp1),
            rr_tp2=float(rr_tp2),
            entry_type=entry_type,
            htf_alignment_count=htf_alignment_count,
            htf_conflict=htf_conflict,
            structure_hits=structure_hits,
            entry_hits=entry_hits,
            trend_hits=trend_hits,
        )

    def _top_real_confluences(self, winner: SignalScore) -> list[str]:
        items = (
            winner.ict_scores
            + winner.structure_scores
            + winner.trend_scores
            + winner.momentum_scores
            + winner.volume_scores
            + winner.volatility_scores
            + winner.fibonacci_scores
        )
        triggered = [s for s in items if s.triggered and s.score > 0]
        triggered.sort(key=lambda item: int(item.score), reverse=True)
        return [f"{s.name}: {s.details}" if s.details else s.name for s in triggered[:8]]

    def _build_snapshot(self, candles: list[Candle], timeframe: str) -> dict:
        tail = candles[-5:]
        return {
            "candles": [
                {
                    "timestamp": c["timestamp"],
                    "open": c["open"],
                    "high": c["high"],
                    "low": c["low"],
                    "close": c["close"],
                    "volume": c["volume"],
                }
                for c in tail
            ],
            "current_price": float(candles[-1]["close"]),
            "timeframe": timeframe,
        }

    def _initial_status(self, current_price: float, zone_low: float, zone_high: float) -> str:
        if zone_low <= current_price <= zone_high:
            return "ARMED"
        return "CREATED"

    @staticmethod
    def _calc_rr(entry: float, stop_loss: float, take_profit: float | None) -> Optional[float]:
        try:
            if take_profit is None:
                return None
            risk = abs(float(entry) - float(stop_loss))
            if risk <= 0:
                return None
            reward = abs(float(take_profit) - float(entry))
            return round(reward / risk, 2)
        except Exception:
            return None
