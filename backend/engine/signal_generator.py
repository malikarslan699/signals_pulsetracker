"""
PulseSignal Pro — Signal Generator

Converts MasterScorer output into actionable trading signals.
Handles multi-timeframe analysis, confidence boosting from HTF alignment,
signal deduplication, and expiry calculation.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional

import numpy as np

from .scoring.scorer import MasterScorer, SignalScore
from .candle_utils import Candle


# ---------------------------------------------------------------------------
# GeneratedSignal — the final deliverable
# ---------------------------------------------------------------------------

@dataclass
class GeneratedSignal:
    """
    A fully resolved trading signal, ready for:
      - Database storage (all fields JSON-serialisable)
      - Telegram / Discord alert formatting
      - Front-end signal card rendering
      - Webhook delivery to subscribers
    """

    # Identity
    id: str                     # UUID4 string
    symbol: str                 # e.g. 'BTCUSDT', 'EURUSD'
    market: str                 # 'crypto' | 'forex' | 'stocks'
    direction: str              # 'LONG' | 'SHORT'
    timeframe: str              # e.g. '1H', '4H'

    # Confidence
    confidence: int             # 0-100
    confidence_band: str        # 'ULTRA_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NO_SIGNAL'
    raw_score: int
    max_possible_score: int

    # Trade levels
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    rr_ratio: float             # Risk-to-reward based on TP2

    # Detailed breakdown (stored as JSON in DB)
    score_breakdown: dict       # {indicator_name: {score, triggered, details}}
    ict_zones: dict             # ICT overlay data for charts
    mtf_analysis: dict          # {tf: {long_confidence, short_confidence, aligned}}
    candle_snapshot: dict       # last 5 candles + current price

    # Human-readable output
    top_confluences: list[str]  # top 8 triggered indicators

    # Timestamps
    fired_at: str               # ISO 8601 UTC
    expires_at: str             # ISO 8601 UTC

    def to_dict(self) -> dict:
        """Return a plain dict safe for JSON serialisation."""
        return asdict(self)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Return True if the signal has passed its expiry time."""
        if now is None:
            now = datetime.now(timezone.utc)
        try:
            exp = datetime.fromisoformat(self.expires_at)
            # Ensure timezone-aware
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            return now >= exp
        except (ValueError, TypeError):
            return False

    def summary_line(self) -> str:
        """One-line summary for logging / Telegram subject lines."""
        dir_emoji = '🟢' if self.direction == 'LONG' else '🔴'
        band_emoji = {
            'ULTRA_HIGH': '⚡', 'HIGH': '✅', 'MEDIUM': '🔶',
            'LOW': '⚠️', 'NO_SIGNAL': '❌',
        }.get(self.confidence_band, '')
        return (
            f"{dir_emoji} {self.direction} {self.symbol} {self.timeframe} "
            f"{band_emoji} {self.confidence_band} ({self.confidence}%) "
            f"| Entry: {self.entry:.5g} | SL: {self.stop_loss:.5g} "
            f"| TP2: {self.take_profit_2:.5g} | RR: {self.rr_ratio:.1f}R"
        )


# ---------------------------------------------------------------------------
# Signal Generator
# ---------------------------------------------------------------------------

class SignalGenerator:
    """
    Generates trading signals from OHLCV candle data.

    Typical usage (single timeframe)
    ---------------------------------
    generator = SignalGenerator()
    signal = generator.generate(
        symbol='BTCUSDT',
        market='crypto',
        candles=candle_list,
        timeframe='1H',
    )
    if signal:
        print(signal.summary_line())

    Multi-timeframe usage
    ----------------------
    signals = generator.generate_multi_timeframe(
        symbol='BTCUSDT',
        market='crypto',
        candles_by_tf={'5m': ..., '15m': ..., '1H': ..., '4H': ..., '1D': ...},
        primary_tf='1H',
    )
    """

    # Minimum confidence required to emit a signal (0-100).
    # Runtime scanner task can override this from admin config.
    MIN_CONFIDENCE: int = 60

    # Minimum gap between long and short confidence to avoid ambiguous calls
    MIN_DIRECTION_GAP: int = 12

    # Timeframe reliability weights used in MTF confidence boost calculation
    TF_WEIGHTS: dict[str, float] = {
        '1m':  0.5,
        '3m':  0.6,
        '5m':  0.8,
        '15m': 1.0,
        '30m': 1.1,
        '1H':  1.2,
        '2H':  1.3,
        '4H':  1.5,
        '8H':  1.7,
        '1D':  2.0,
        '1W':  2.5,
    }

    # How long a signal is valid after firing, per timeframe
    TF_EXPIRY_HOURS: dict[str, int] = {
        '1m':  0,    # 30 minutes → set as fraction below
        '3m':  1,
        '5m':  1,
        '15m': 4,
        '30m': 8,
        '1H':  24,
        '2H':  48,
        '4H':  96,
        '8H':  192,
        '1D':  240,
        '1W':  720,
    }

    # Fractional expiry for very short timeframes (minutes)
    TF_EXPIRY_MINUTES: dict[str, int] = {
        '1m':  30,
        '3m':  60,
    }

    def __init__(self) -> None:
        self.scorer = MasterScorer()

    # -----------------------------------------------------------------------
    # Primary public method — single timeframe
    # -----------------------------------------------------------------------

    def generate(
        self,
        symbol: str,
        market: str,
        candles: list[Candle],
        timeframe: str,
        candles_by_tf: Optional[dict[str, list[Candle]]] = None,
    ) -> Optional[GeneratedSignal]:
        """
        Analyse ``candles`` on ``timeframe`` and return a signal if the
        confidence threshold is met.

        Parameters
        ----------
        symbol : str
            Instrument ticker, e.g. ``'BTCUSDT'`` or ``'EURUSD'``.
        market : str
            Market category — ``'crypto'``, ``'forex'``, or ``'stocks'``.
        candles : list[Candle]
            Primary timeframe OHLCV history, **ascending** order.
            Minimum 50 candles required.
        timeframe : str
            Candle interval key, e.g. ``'1H'``, ``'4H'``, ``'1D'``.
        candles_by_tf : dict[str, list[Candle]], optional
            Candles for other timeframes to run MTF confluence analysis.
            Keys must be timeframe strings; each list needs ≥ 50 candles.

        Returns
        -------
        GeneratedSignal or None
            A fully populated signal if confidence ≥ MIN_CONFIDENCE and
            there is a clear directional edge, else ``None``.
        """
        if len(candles) < 50:
            return None

        # ── Convert candle list to numpy arrays ────────────────────────────
        opens      = np.array([c['open']      for c in candles], dtype=np.float64)
        highs      = np.array([c['high']      for c in candles], dtype=np.float64)
        lows       = np.array([c['low']       for c in candles], dtype=np.float64)
        closes     = np.array([c['close']     for c in candles], dtype=np.float64)
        volumes    = np.array([c['volume']    for c in candles], dtype=np.float64)
        timestamps = np.array([c['timestamp'] for c in candles], dtype=np.float64)

        # ── Score primary timeframe ────────────────────────────────────────
        try:
            long_score, short_score = self.scorer.score(
                opens, highs, lows, closes, volumes, timestamps,
                timeframe, symbol,
            )
        except Exception:
            return None

        long_c = long_score.confidence
        short_c = short_score.confidence

        # ── Directional clarity check ──────────────────────────────────────
        # Both directions must be below the threshold, OR the gap must be
        # meaningful enough to indicate a genuine edge.
        best_conf = max(long_c, short_c)
        if best_conf < self.MIN_CONFIDENCE:
            return None

        if abs(long_c - short_c) < self.MIN_DIRECTION_GAP:
            return None

        winner: SignalScore = long_score if long_c >= short_c else short_score

        # ── Multi-timeframe analysis ───────────────────────────────────────
        mtf_analysis: dict[str, dict] = {}
        if candles_by_tf:
            for tf, tf_candles in candles_by_tf.items():
                if tf == timeframe or len(tf_candles) < 50:
                    continue
                try:
                    tf_opens      = np.array([c['open']      for c in tf_candles], dtype=np.float64)
                    tf_highs      = np.array([c['high']      for c in tf_candles], dtype=np.float64)
                    tf_lows       = np.array([c['low']       for c in tf_candles], dtype=np.float64)
                    tf_closes     = np.array([c['close']     for c in tf_candles], dtype=np.float64)
                    tf_volumes    = np.array([c['volume']    for c in tf_candles], dtype=np.float64)
                    tf_timestamps = np.array([c['timestamp'] for c in tf_candles], dtype=np.float64)

                    tf_long, tf_short = self.scorer.score(
                        tf_opens, tf_highs, tf_lows, tf_closes,
                        tf_volumes, tf_timestamps, tf, symbol,
                    )
                    tf_aligned = (
                        (winner.direction == 'LONG'  and tf_long.confidence  > tf_short.confidence) or
                        (winner.direction == 'SHORT' and tf_short.confidence > tf_long.confidence)
                    )
                    mtf_analysis[tf] = {
                        'long_confidence':  tf_long.confidence,
                        'short_confidence': tf_short.confidence,
                        'direction': 'LONG' if tf_long.confidence > tf_short.confidence else 'SHORT',
                        'aligned': tf_aligned,
                        'weight': self.TF_WEIGHTS.get(tf, 1.0),
                    }
                except Exception:
                    pass

        # ── MTF confidence boost ───────────────────────────────────────────
        # Each aligned higher-timeframe (weight ≥ 1.2) adds a small bonus.
        aligned_htf_count = sum(
            1 for tf, data in mtf_analysis.items()
            if data.get('aligned') and self.TF_WEIGHTS.get(tf, 1.0) >= 1.2
        )
        aligned_ltf_count = sum(
            1 for tf, data in mtf_analysis.items()
            if data.get('aligned') and self.TF_WEIGHTS.get(tf, 1.0) < 1.2
        )

        if aligned_htf_count >= 3:
            boost = 8
        elif aligned_htf_count == 2:
            boost = 5
        elif aligned_htf_count == 1:
            boost = 2
        else:
            boost = 0

        # Minor additional boost if LTFs also agree
        if aligned_ltf_count >= 2:
            boost += 2
        elif aligned_ltf_count == 1:
            boost += 1

        final_confidence = min(100, winner.confidence + boost)

        # Re-check threshold after boost
        if final_confidence < self.MIN_CONFIDENCE:
            return None

        # ── Multi-timeframe confirmation gate ─────────────────────────
        # For lower timeframes, require higher-TF alignment to confirm the
        # trend bias before accepting the signal.  If the required HTF is
        # present in mtf_analysis but NOT aligned, the signal is rejected.
        #
        #   5m  signal → 15m must be aligned
        #   15m signal → 1H  must be aligned
        #   1H  signal → 4H  must be aligned
        #   4H+ signal → no mandatory gate (already a higher-TF decision)
        MTF_GATES: dict[str, str] = {
            # Keep strict confirmation on the noisiest TF only.
            '5m': '15m',
        }
        required_tf = MTF_GATES.get(timeframe)
        if required_tf and required_tf in mtf_analysis:
            if not mtf_analysis[required_tf].get('aligned'):
                return None  # HTF disagrees — do not fire

        # ── Low-volatility gate ────────────────────────────────────────────
        # Avoid signals in dead/flat zones — choppy price action kills RR.
        try:
            from .indicators.volatility import atr_analysis as _atr_fn
            _atr_info = _atr_fn(highs, lows, closes, float(closes[-1]), winner.direction)
            _atr_pct = _atr_info.get('atr_pct', 0.0)
            if isinstance(_atr_pct, float) and _atr_pct < 0.25:
                return None  # ATR < 0.25% of price — too flat/choppy
        except Exception:
            pass

        # ── Minimum R:R gate ──────────────────────────────────────────────
        # Only fire if TP distance is at least 1.5× the SL distance.
        if winner.rr_ratio < 1.5:
            return None

        # ── Trend alignment gate ──────────────────────────────────────────
        # Require at least one trend indicator OR two ICT/structure confirms
        # aligned with signal direction. Blocks pure counter-trend signals.
        trend_hits = sum(1 for s in winner.trend_scores if s.triggered and s.score > 0)
        ict_hits = sum(1 for s in winner.ict_scores if s.triggered and s.score > 0)
        struct_hits = sum(1 for s in winner.structure_scores if s.triggered and s.score > 0)
        if trend_hits == 0 and (ict_hits + struct_hits) < 1:
            return None  # No trend and no ICT/structure support — reject

        # ── Candle snapshot (last 5 candles) ──────────────────────────────
        snapshot_candles = candles[-5:]
        candle_snapshot = {
            'candles': [
                {
                    'timestamp': c['timestamp'],
                    'open':   c['open'],
                    'high':   c['high'],
                    'low':    c['low'],
                    'close':  c['close'],
                    'volume': c['volume'],
                }
                for c in snapshot_candles
            ],
            'current_price': float(closes[-1]),
            'timeframe': timeframe,
        }

        # ── Expiry timestamp ──────────────────────────────────────────────
        now = datetime.now(timezone.utc)

        if timeframe in self.TF_EXPIRY_MINUTES:
            expires_at = now + timedelta(minutes=self.TF_EXPIRY_MINUTES[timeframe])
        else:
            expiry_hours = self.TF_EXPIRY_HOURS.get(timeframe, 24)
            expires_at = now + timedelta(hours=expiry_hours)

        # ── Assemble and return ───────────────────────────────────────────
        return GeneratedSignal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            market=market,
            direction=winner.direction,
            timeframe=timeframe,
            confidence=final_confidence,
            confidence_band=winner.confidence_band,
            entry=winner.entry,
            stop_loss=winner.stop_loss,
            take_profit_1=winner.take_profit_1,
            take_profit_2=winner.take_profit_2,
            take_profit_3=winner.take_profit_3,
            rr_ratio=winner.rr_ratio,
            raw_score=winner.raw_score,
            max_possible_score=winner.max_possible,
            score_breakdown=winner.to_breakdown_dict(),
            ict_zones=winner.ict_zones,
            mtf_analysis=mtf_analysis,
            candle_snapshot=candle_snapshot,
            top_confluences=winner.top_confluences,
            fired_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )

    # -----------------------------------------------------------------------
    # Multi-timeframe sweep
    # -----------------------------------------------------------------------

    def generate_multi_timeframe(
        self,
        symbol: str,
        market: str,
        candles_by_tf: dict[str, list[Candle]],
        primary_tf: str = '1H',
    ) -> list[GeneratedSignal]:
        """
        Run analysis across every provided timeframe and return all signals
        that meet the confidence threshold.

        For each timeframe, all *other* timeframes are passed as MTF context.
        Duplicate directions are deduplicated: if LONG signals fire on
        multiple timeframes, only the highest-confidence one is kept.

        Parameters
        ----------
        symbol : str
            Instrument ticker.
        market : str
            Market category.
        candles_by_tf : dict[str, list[Candle]]
            Dict mapping timeframe strings to candle lists.
        primary_tf : str
            The most important timeframe — currently used only for ordering.

        Returns
        -------
        list[GeneratedSignal]
            0, 1, or 2 signals (at most one LONG and one SHORT), sorted by
            timeframe weight descending.
        """
        raw_signals: list[GeneratedSignal] = []

        for tf, candles in candles_by_tf.items():
            context = {k: v for k, v in candles_by_tf.items() if k != tf}
            signal = self.generate(
                symbol=symbol,
                market=market,
                candles=candles,
                timeframe=tf,
                candles_by_tf=context if context else None,
            )
            if signal:
                raw_signals.append(signal)

        if not raw_signals:
            return []

        # ── Deduplication: keep highest-confidence signal per direction ────
        best_by_direction: dict[str, GeneratedSignal] = {}
        for sig in sorted(raw_signals, key=lambda s: s.confidence, reverse=True):
            if sig.direction not in best_by_direction:
                best_by_direction[sig.direction] = sig

        deduped = list(best_by_direction.values())

        # ── Sort: heavier timeframes first, then by confidence ────────────
        deduped.sort(
            key=lambda s: (
                -self.TF_WEIGHTS.get(s.timeframe, 1.0),
                -s.confidence,
            )
        )

        return deduped

    # -----------------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------------

    def get_best_signal(
        self,
        symbol: str,
        market: str,
        candles_by_tf: dict[str, list[Candle]],
    ) -> Optional[GeneratedSignal]:
        """
        Run MTF analysis and return the single highest-confidence signal,
        regardless of direction.  Returns ``None`` if no signal qualifies.
        """
        signals = self.generate_multi_timeframe(symbol, market, candles_by_tf)
        if not signals:
            return None
        return max(signals, key=lambda s: s.confidence)

    def batch_generate(
        self,
        requests: list[dict],
    ) -> list[Optional[GeneratedSignal]]:
        """
        Process multiple generate() requests in sequence.

        Parameters
        ----------
        requests : list[dict]
            Each dict must contain the keyword arguments accepted by
            :meth:`generate`: ``symbol``, ``market``, ``candles``,
            ``timeframe``, and optionally ``candles_by_tf``.

        Returns
        -------
        list[Optional[GeneratedSignal]]
            One entry per request (``None`` where no signal was produced).
        """
        results: list[Optional[GeneratedSignal]] = []
        for req in requests:
            try:
                sig = self.generate(
                    symbol=req['symbol'],
                    market=req['market'],
                    candles=req['candles'],
                    timeframe=req['timeframe'],
                    candles_by_tf=req.get('candles_by_tf'),
                )
            except Exception:
                sig = None
            results.append(sig)
        return results

    @staticmethod
    def filter_by_band(
        signals: list[GeneratedSignal],
        min_band: str = 'MEDIUM',
    ) -> list[GeneratedSignal]:
        """
        Filter a list of signals by minimum confidence band.

        Band order (ascending): NO_SIGNAL < LOW < MEDIUM < HIGH < ULTRA_HIGH.
        """
        band_rank: dict[str, int] = {
            'NO_SIGNAL': 0,
            'LOW':       1,
            'MEDIUM':    2,
            'HIGH':      3,
            'ULTRA_HIGH': 4,
        }
        min_rank = band_rank.get(min_band, 0)
        return [
            s for s in signals
            if band_rank.get(s.confidence_band, 0) >= min_rank
        ]

    @staticmethod
    def format_telegram_message(signal: GeneratedSignal) -> str:
        """
        Render a Telegram-ready message string for the given signal.

        Uses Markdown V2 compatible formatting (no parse_mode escaping
        applied here — callers must handle that if needed).
        """
        dir_emoji = '🟢' if signal.direction == 'LONG' else '🔴'
        band_emoji = {
            'ULTRA_HIGH': '⚡',
            'HIGH':       '✅',
            'MEDIUM':     '🔶',
            'LOW':        '⚠️',
            'NO_SIGNAL':  '❌',
        }.get(signal.confidence_band, '')

        lines = [
            f"{dir_emoji} *{signal.symbol}* — {signal.direction} Signal",
            f"📊 Timeframe: `{signal.timeframe}` | Market: `{signal.market.upper()}`",
            f"{band_emoji} Confidence: *{signal.confidence}%* ({signal.confidence_band})",
            "",
            "📐 *Trade Levels*",
            f"  Entry:  `{signal.entry:.5g}`",
            f"  Stop:   `{signal.stop_loss:.5g}`",
            f"  TP1:    `{signal.take_profit_1:.5g}`",
            f"  TP2:    `{signal.take_profit_2:.5g}`",
            f"  TP3:    `{signal.take_profit_3:.5g}`",
            f"  R/R:    `{signal.rr_ratio:.1f}R`",
            "",
            "🔑 *Top Confluences*",
        ]
        for c in signal.top_confluences[:6]:
            lines.append(f"  • {c}")

        # MTF alignment summary
        aligned_tfs = [
            tf for tf, data in signal.mtf_analysis.items()
            if data.get('aligned')
        ]
        if aligned_tfs:
            lines.append("")
            lines.append(f"📡 HTF Aligned: {', '.join(sorted(aligned_tfs))}")

        lines.append("")
        lines.append(f"🕐 Fired: `{signal.fired_at[:19]} UTC`")
        lines.append(f"⏳ Expires: `{signal.expires_at[:19]} UTC`")
        lines.append("")
        lines.append("_PulseSignal Pro — signals.pulsetracker.net_")

        return "\n".join(lines)
