"""
PulseSignal Pro — Master Scoring Engine

Aggregates ALL indicator results into a single confidence score (0-100).

MAX POSSIBLE SCORES by category:
  ICT Smart Money:     120 points max  (8 components)
  Market Structure:     45 points max  (4 components)
  Trend Indicators:     46 points max  (5 components)
  Momentum:             52 points max  (6 components)
  Volatility:           34 points max  (4 components)
  Volume:               31 points max  (4 components)
  Fibonacci:            10 points max  (1 component)
  ─────────────────────────────────────────────────
  TOTAL MAX:           ~338 points  → normalized to 0-100
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# Make sibling packages importable when the file is executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class IndicatorScore:
    """Score contribution from a single indicator."""
    name: str
    category: str
    score: int
    max_score: int
    triggered: bool
    details: str = ""


@dataclass
class SignalScore:
    """
    Full scoring result for one direction (LONG or SHORT).

    Populated by MasterScorer.score() and consumed by SignalGenerator.
    """
    direction: str              # 'LONG' or 'SHORT'
    raw_score: int              # sum of all triggered indicator scores
    max_possible: int           # theoretical max for the direction
    confidence: int             # 0-100 normalised value
    confidence_band: str        # 'ULTRA_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NO_SIGNAL'

    # Per-category breakdowns
    ict_scores: list[IndicatorScore] = field(default_factory=list)
    structure_scores: list[IndicatorScore] = field(default_factory=list)
    trend_scores: list[IndicatorScore] = field(default_factory=list)
    momentum_scores: list[IndicatorScore] = field(default_factory=list)
    volatility_scores: list[IndicatorScore] = field(default_factory=list)
    volume_scores: list[IndicatorScore] = field(default_factory=list)
    fibonacci_scores: list[IndicatorScore] = field(default_factory=list)

    # ICT zone snapshots for chart overlay
    ict_zones: dict = field(default_factory=dict)

    # Human-readable top confluences for Telegram / UI cards
    top_confluences: list[str] = field(default_factory=list)

    # Trade levels (populated inside build_score)
    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    rr_ratio: float = 0.0

    # ---------------------------------------------------------------------------
    def to_breakdown_dict(self) -> dict:
        """
        Flatten all category scores into a single dict suitable for database
        storage (JSON column).

        Structure:
          { "<indicator_name>": {"score": int, "triggered": bool, "details": str}, ... }
        """
        result: dict = {}
        all_cats = (
            self.ict_scores,
            self.structure_scores,
            self.trend_scores,
            self.momentum_scores,
            self.volatility_scores,
            self.volume_scores,
            self.fibonacci_scores,
        )
        for cat_scores in all_cats:
            for s in cat_scores:
                # Use "category/name" as key to avoid collisions
                key = f"{s.category}/{s.name}"
                result[key] = {
                    "score": s.score,
                    "max_score": s.max_score,
                    "triggered": s.triggered,
                    "details": s.details,
                }
        return result


# ---------------------------------------------------------------------------
# Master Scorer
# ---------------------------------------------------------------------------

class MasterScorer:
    """
    Orchestrates all indicator modules and aggregates their outputs into
    a pair of SignalScore objects (LONG, SHORT) for a given candle series.

    Usage
    -----
    scorer = MasterScorer()
    long_score, short_score = scorer.score(opens, highs, lows, closes,
                                            volumes, timestamps, '1H', 'BTCUSDT')
    """

    # Minimum candle count before we attempt any analysis
    MIN_CANDLES: int = 50

    def __init__(self) -> None:
        # ── Trend ──────────────────────────────────────────────────────────
        from ..indicators.trend import (
            ema_stack,
            supertrend,
            ichimoku,
        )
        # ── Momentum ───────────────────────────────────────────────────────
        from ..indicators.momentum import (
            rsi_analysis,
            macd,
            mfi,
        )
        # ── Volatility ─────────────────────────────────────────────────────
        from ..indicators.volatility import (
            bollinger_bands,
            keltner_channels,
            atr_analysis,
        )
        # ── Volume ─────────────────────────────────────────────────────────
        from ..indicators.volume import (
            volume_spike,
            vwap,
        )
        # ── Structure ──────────────────────────────────────────────────────
        from ..indicators.structure import (
            detect_market_structure,
            detect_support_resistance,
        )
        # ── Fibonacci ──────────────────────────────────────────────────────
        from ..indicators.fibonacci import find_fib_retracement_zone
        # ── ICT ────────────────────────────────────────────────────────────
        from ..ict.order_blocks import detect_order_blocks
        from ..ict.fair_value_gaps import detect_fvg
        from ..ict.liquidity import detect_liquidity_zones
        from ..ict.ote import detect_ote
        from ..ict.killzones import is_in_killzone
        from ..ict.premium_discount import analyze_premium_discount
        from ..ict.breaker_blocks import detect_breaker_blocks
        from ..ict.daily_bias import analyze_daily_bias

        # Store references to avoid repeated imports on every call
        self._ema_stack = ema_stack
        self._supertrend = supertrend
        self._ichimoku = ichimoku
        self._rsi_analysis = rsi_analysis
        self._macd = macd
        self._mfi = mfi
        self._bollinger_bands = bollinger_bands
        self._keltner_channels = keltner_channels
        self._atr_analysis = atr_analysis
        self._volume_spike = volume_spike
        self._vwap = vwap
        self._detect_market_structure = detect_market_structure
        self._detect_support_resistance = detect_support_resistance
        self._find_fib_zone = find_fib_retracement_zone
        self._detect_order_blocks = detect_order_blocks
        self._detect_fvg = detect_fvg
        self._detect_liquidity = detect_liquidity_zones
        self._detect_ote = detect_ote
        self._is_in_killzone = is_in_killzone
        self._analyze_pd = analyze_premium_discount
        self._detect_breakers = detect_breaker_blocks
        self._analyze_bias = analyze_daily_bias

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def score(
        self,
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: np.ndarray,
        timeframe: str = '1H',
        symbol: str = '',
    ) -> tuple[SignalScore, SignalScore]:
        """
        Run every indicator, aggregate the outputs, and return a pair of
        ``(long_signal_score, short_signal_score)``.

        Parameters
        ----------
        opens, highs, lows, closes, volumes : array-like
            OHLCV data arrays of equal length, in ascending chronological order.
        timestamps : array-like
            Unix millisecond timestamps for each candle.
        timeframe : str
            One of '5m', '15m', '1H', '4H', '1D'.
        symbol : str
            Instrument identifier — used for informational fields only.

        Returns
        -------
        tuple[SignalScore, SignalScore]
            ``(long_score, short_score)`` — both always present; use the
            ``confidence`` field to decide which (if any) is actionable.
        """
        from .normalizer import normalize_score, score_to_confidence_band

        # ── Guard: minimum candles ──────────────────────────────────────────
        if len(closes) < self.MIN_CANDLES:
            return self._empty_score('LONG'), self._empty_score('SHORT')

        # ── Convert to float64 numpy arrays ────────────────────────────────
        opens = np.asarray(opens, dtype=np.float64)
        highs = np.asarray(highs, dtype=np.float64)
        lows = np.asarray(lows, dtype=np.float64)
        closes = np.asarray(closes, dtype=np.float64)
        volumes = np.asarray(volumes, dtype=np.float64)
        timestamps = np.asarray(timestamps, dtype=np.float64)

        ict_zones: dict = {}
        ict_long: list[IndicatorScore] = []
        ict_short: list[IndicatorScore] = []

        # ================================================================
        # SECTION 1 — ICT SMART MONEY  (max ~120 pts)
        # ================================================================

        # ── 1a. Order Blocks ────────────────────────────────────────────
        try:
            ob = self._detect_order_blocks(
                opens, highs, lows, closes, volumes, timestamps
            )
            ict_zones['order_blocks'] = {
                'bullish': [
                    {'high': o.high, 'low': o.low, 'strength': o.strength,
                     'times_tested': o.times_tested}
                    for o in ob.get('bullish_obs', [])[:5]
                ],
                'bearish': [
                    {'high': o.high, 'low': o.low, 'strength': o.strength,
                     'times_tested': o.times_tested}
                    for o in ob.get('bearish_obs', [])[:5]
                ],
            }
            in_bull_ob = ob.get('price_in_bullish_ob', False)
            in_bear_ob = ob.get('price_in_bearish_ob', False)
            ict_long.append(IndicatorScore(
                name='ICT Order Block', category='ICT',
                score=ob.get('score_long', 0), max_score=25,
                triggered=in_bull_ob,
                details='Fresh bullish OB' if in_bull_ob else 'Nearby bullish OB',
            ))
            ict_short.append(IndicatorScore(
                name='ICT Order Block', category='ICT',
                score=ob.get('score_short', 0), max_score=25,
                triggered=in_bear_ob,
                details='Fresh bearish OB' if in_bear_ob else 'Nearby bearish OB',
            ))
        except Exception:
            pass

        # ── 1b. Fair Value Gaps ─────────────────────────────────────────
        try:
            fvg = self._detect_fvg(highs, lows, closes, timestamps)
            ict_zones['fvg'] = {
                'bullish': [
                    {'top': g.top, 'bottom': g.bottom, 'fill_pct': g.fill_pct}
                    for g in fvg.get('unfilled_bullish', [])[:5]
                ],
                'bearish': [
                    {'top': g.top, 'bottom': g.bottom, 'fill_pct': g.fill_pct}
                    for g in fvg.get('unfilled_bearish', [])[:5]
                ],
            }
            in_bull_fvg = fvg.get('price_in_bullish_fvg', False)
            in_bear_fvg = fvg.get('price_in_bearish_fvg', False)
            ict_long.append(IndicatorScore(
                name='ICT Fair Value Gap', category='ICT',
                score=fvg.get('score_long', 0), max_score=15,
                triggered=in_bull_fvg,
                details='Price in bullish FVG' if in_bull_fvg else '',
            ))
            ict_short.append(IndicatorScore(
                name='ICT Fair Value Gap', category='ICT',
                score=fvg.get('score_short', 0), max_score=15,
                triggered=in_bear_fvg,
                details='Price in bearish FVG' if in_bear_fvg else '',
            ))
        except Exception:
            pass

        # ── 1c. Liquidity Zones / Grabs ─────────────────────────────────
        try:
            liq = self._detect_liquidity(highs, lows, closes, timestamps)
            ict_zones['liquidity'] = {
                'bsl': [z.price for z in liq.get('bsl_zones', [])[:5]],
                'ssl': [z.price for z in liq.get('ssl_zones', [])[:5]],
                'equal_highs': [
                    {'price': z.price, 'strength': z.strength}
                    for z in liq.get('equal_highs', [])[:3]
                ],
                'equal_lows': [
                    {'price': z.price, 'strength': z.strength}
                    for z in liq.get('equal_lows', [])[:3]
                ],
                'pdh': liq.get('pdh'),
                'pdl': liq.get('pdl'),
            }
            grab_bull = liq.get('liquidity_grab_bull', False)
            grab_bear = liq.get('liquidity_grab_bear', False)
            ict_long.append(IndicatorScore(
                name='ICT Liquidity Grab', category='ICT',
                score=liq.get('score_long', 0), max_score=20,
                triggered=grab_bull,
                details='Bullish liquidity grab detected' if grab_bull else
                        ('Approaching SSL' if liq.get('approaching_ssl') else ''),
            ))
            ict_short.append(IndicatorScore(
                name='ICT Liquidity Grab', category='ICT',
                score=liq.get('score_short', 0), max_score=20,
                triggered=grab_bear,
                details='Bearish liquidity grab detected' if grab_bear else
                        ('Approaching BSL' if liq.get('approaching_bsl') else ''),
            ))
        except Exception:
            pass

        # ── 1d. Optimal Trade Entry (OTE) ────────────────────────────────
        try:
            ote = self._detect_ote(highs, lows, closes, timestamps)
            active_setup = ote.get('active_setup')
            ict_zones['ote'] = {
                'active': ote.get('price_in_ote', False),
                'low': ote.get('ote_low'),
                'high': ote.get('ote_high'),
                'direction': active_setup.direction if active_setup else None,
                'quality': active_setup.quality if active_setup else None,
            }
            in_bull_ote = (
                ote.get('price_in_ote', False)
                and active_setup is not None
                and active_setup.direction == 'bullish'
            )
            in_bear_ote = (
                ote.get('price_in_ote', False)
                and active_setup is not None
                and active_setup.direction == 'bearish'
            )
            quality_label = (
                f"Quality: {active_setup.quality}" if active_setup else ''
            )
            ict_long.append(IndicatorScore(
                name='ICT OTE Zone', category='ICT',
                score=ote.get('score_long', 0), max_score=20,
                triggered=in_bull_ote,
                details=f'Price in bullish OTE zone. {quality_label}' if in_bull_ote else '',
            ))
            ict_short.append(IndicatorScore(
                name='ICT OTE Zone', category='ICT',
                score=ote.get('score_short', 0), max_score=20,
                triggered=in_bear_ote,
                details=f'Price in bearish OTE zone. {quality_label}' if in_bear_ote else '',
            ))
        except Exception:
            pass

        # ── 1e. Killzones (session timing) ───────────────────────────────
        try:
            kz = self._is_in_killzone()
            kz_score = kz.score_bonus if kz.in_killzone and kz.score_bonus > 0 else 0
            kz_triggered = kz.in_killzone and kz.session_quality == 'high'
            kz_detail = (
                f"{kz.session_name} — {kz.session_quality} quality"
                if kz.in_killzone else
                f"Off-hours (next: {kz.next_kz_name} in {kz.time_to_next_kz}min)"
            )
            ict_long.append(IndicatorScore(
                name='ICT Killzone', category='ICT',
                score=kz_score, max_score=10,
                triggered=kz_triggered,
                details=kz_detail,
            ))
            ict_short.append(IndicatorScore(
                name='ICT Killzone', category='ICT',
                score=kz_score, max_score=10,
                triggered=kz_triggered,
                details=kz_detail,
            ))
        except Exception:
            pass

        # ── 1f. Premium / Discount Array ─────────────────────────────────
        try:
            pd_res = self._analyze_pd(highs, lows, closes)
            ict_zones['premium_discount'] = {
                'zone': pd_res.zone,
                'current_pct': pd_res.current_pct,
                'equilibrium': pd_res.equilibrium,
                'swing_high': pd_res.swing_high,
                'swing_low': pd_res.swing_low,
                'fib_levels': {
                    '0.236': pd_res.fib_236,
                    '0.382': pd_res.fib_382,
                    '0.500': pd_res.fib_500,
                    '0.618': pd_res.fib_618,
                    '0.786': pd_res.fib_786,
                },
            }
            pct_disp = pd_res.current_pct * 100
            ict_long.append(IndicatorScore(
                name='ICT Premium/Discount', category='ICT',
                score=pd_res.score_long, max_score=12,
                triggered=pd_res.is_discount,
                details=f'Price in {pd_res.zone} zone ({pct_disp:.0f}% of range)',
            ))
            ict_short.append(IndicatorScore(
                name='ICT Premium/Discount', category='ICT',
                score=pd_res.score_short, max_score=12,
                triggered=pd_res.is_premium,
                details=f'Price in {pd_res.zone} zone ({pct_disp:.0f}% of range)',
            ))
        except Exception:
            pass

        # ── 1g. Breaker Blocks ──────────────────────────────────────────
        try:
            bb_res = self._detect_breakers(opens, highs, lows, closes, timestamps)
            at_bull_bb = bb_res.get('price_at_bullish_breaker', False)
            at_bear_bb = bb_res.get('price_at_bearish_breaker', False)
            ict_long.append(IndicatorScore(
                name='ICT Breaker Block', category='ICT',
                score=bb_res.get('score_long', 0), max_score=15,
                triggered=at_bull_bb,
                details='Price at bullish breaker block' if at_bull_bb else '',
            ))
            ict_short.append(IndicatorScore(
                name='ICT Breaker Block', category='ICT',
                score=bb_res.get('score_short', 0), max_score=15,
                triggered=at_bear_bb,
                details='Price at bearish breaker block' if at_bear_bb else '',
            ))
        except Exception:
            pass

        # ── 1h. Daily Bias ──────────────────────────────────────────────
        try:
            bias = self._analyze_bias(highs, lows, closes, timestamps, timeframe)
            ict_zones['daily_bias'] = {
                'bias': bias.bias,
                'confidence': bias.confidence,
                'pdh': bias.pdh,
                'pdl': bias.pdl,
                'weekly_trend': bias.weekly_trend,
                'swept_pdh': bias.swept_pdh,
                'swept_pdl': bias.swept_pdl,
            }
            bias_detail = (
                f"Daily bias: {bias.bias} ({bias.confidence}% confidence)"
                + (f" | Weekly: {bias.weekly_trend}" if bias.weekly_trend != 'neutral' else '')
            )
            ict_long.append(IndicatorScore(
                name='ICT Daily Bias', category='ICT',
                score=bias.score_long, max_score=15,
                triggered=bias.bias == 'bullish',
                details=bias_detail,
            ))
            ict_short.append(IndicatorScore(
                name='ICT Daily Bias', category='ICT',
                score=bias.score_short, max_score=15,
                triggered=bias.bias == 'bearish',
                details=bias_detail,
            ))
        except Exception:
            pass

        # ================================================================
        # SECTION 2 — MARKET STRUCTURE  (max ~45 pts)
        # ================================================================

        struct_long: list[IndicatorScore] = []
        struct_short: list[IndicatorScore] = []

        try:
            ms = self._detect_market_structure(highs, lows, closes, timestamps)
            bos_bull = ms.get('bos_bullish', False) or ms.get('choch_bullish', False)
            bos_bear = ms.get('bos_bearish', False) or ms.get('choch_bearish', False)

            # BOS / CHoCH
            def _bos_detail_long() -> str:
                if ms.get('choch_bullish'):
                    return 'CHoCH Bullish — trend reversal confirmed'
                if ms.get('bos_bullish'):
                    return 'BOS Bullish — continuation above structure'
                return ''

            def _bos_detail_short() -> str:
                if ms.get('choch_bearish'):
                    return 'CHoCH Bearish — trend reversal confirmed'
                if ms.get('bos_bearish'):
                    return 'BOS Bearish — continuation below structure'
                return ''

            struct_long.append(IndicatorScore(
                name='Break of Structure', category='Structure',
                score=ms.get('score_long', 0), max_score=15,
                triggered=bos_bull,
                details=_bos_detail_long(),
            ))
            struct_short.append(IndicatorScore(
                name='Break of Structure', category='Structure',
                score=ms.get('score_short', 0), max_score=15,
                triggered=bos_bear,
                details=_bos_detail_short(),
            ))

            # Trend direction
            trend = ms.get('trend', 'ranging')
            struct_long.append(IndicatorScore(
                name='Market Trend', category='Structure',
                score=8 if trend == 'uptrend' else 0, max_score=8,
                triggered=trend == 'uptrend',
                details=f'Market structure: {trend}',
            ))
            struct_short.append(IndicatorScore(
                name='Market Trend', category='Structure',
                score=8 if trend == 'downtrend' else 0, max_score=8,
                triggered=trend == 'downtrend',
                details=f'Market structure: {trend}',
            ))
        except Exception:
            pass

        try:
            sr = self._detect_support_resistance(highs, lows, closes, timestamps)
            at_sup = sr.get('at_support', False)
            at_res = sr.get('at_resistance', False)
            sr_flip = bool(sr.get('sr_flip'))

            struct_long.append(IndicatorScore(
                name='Support Level', category='Structure',
                score=sr.get('score_long', 0), max_score=10,
                triggered=at_sup,
                details=(
                    f"At support {sr.get('nearest_support', ''):.6g}" if at_sup else ''
                ),
            ))
            struct_short.append(IndicatorScore(
                name='Resistance Level', category='Structure',
                score=sr.get('score_short', 0), max_score=10,
                triggered=at_res,
                details=(
                    f"At resistance {sr.get('nearest_resistance', ''):.6g}" if at_res else ''
                ),
            ))

            # S/R flip (resistance became support or vice versa)
            flip_score = 10 if sr_flip else 0
            struct_long.append(IndicatorScore(
                name='S/R Flip', category='Structure',
                score=flip_score if (
                    at_sup or closes[-1] > sr.get('nearest_support', 0)
                ) else 0,
                max_score=10,
                triggered=sr_flip and at_sup,
                details='Resistance flipped to support' if sr_flip else '',
            ))
            struct_short.append(IndicatorScore(
                name='S/R Flip', category='Structure',
                score=flip_score if (
                    at_res or closes[-1] < sr.get('nearest_resistance', float('inf'))
                ) else 0,
                max_score=10,
                triggered=sr_flip and at_res,
                details='Support flipped to resistance' if sr_flip else '',
            ))
        except Exception:
            pass

        # ================================================================
        # SECTION 3 — TREND INDICATORS  (max ~46 pts)
        # ================================================================

        trend_long: list[IndicatorScore] = []
        trend_short: list[IndicatorScore] = []

        # ── 3a. EMA Stack ─────────────────────────────────────────────────
        try:
            ema_res = self._ema_stack(closes)
            is_bull_stack = ema_res.get('is_bullish_stack', False)
            is_bear_stack = ema_res.get('is_bearish_stack', False)
            bull_cnt = ema_res.get('bullish_count', 0)

            trend_long.append(IndicatorScore(
                name='EMA Stack', category='Trend',
                score=(
                    ema_res.get('score', 0) if (is_bull_stack or bull_cnt >= 3)
                    else 0
                ),
                max_score=10,
                triggered=is_bull_stack,
                details=f"Bullish alignment: {bull_cnt}/4 consecutive EMA pairs",
            ))
            trend_short.append(IndicatorScore(
                name='EMA Stack', category='Trend',
                score=(
                    ema_res.get('score', 0) if is_bear_stack
                    else (5 if bull_cnt <= 1 else 0)
                ),
                max_score=10,
                triggered=is_bear_stack,
                details=f"Bearish alignment: {4 - bull_cnt}/4 consecutive EMA pairs",
            ))
        except Exception:
            pass

        # ── 3b. Supertrend ────────────────────────────────────────────────
        try:
            st = self._supertrend(highs, lows, closes)
            flip_bonus = 5 if st.get('just_flipped') else 0
            trend_long.append(IndicatorScore(
                name='Supertrend', category='Trend',
                score=(10 + flip_bonus) if st.get('is_bullish') else 0,
                max_score=10,
                triggered=st.get('is_bullish', False),
                details=(
                    'Supertrend bullish' +
                    (' — JUST FLIPPED' if st.get('just_flipped') else '')
                ) if st.get('is_bullish') else '',
            ))
            trend_short.append(IndicatorScore(
                name='Supertrend', category='Trend',
                score=(10 + flip_bonus) if st.get('is_bearish') else 0,
                max_score=10,
                triggered=st.get('is_bearish', False),
                details=(
                    'Supertrend bearish' +
                    (' — JUST FLIPPED' if st.get('just_flipped') else '')
                ) if st.get('is_bearish') else '',
            ))
        except Exception:
            pass

        # ── 3c. Ichimoku Cloud ───────────────────────────────────────────
        try:
            ich = self._ichimoku(highs, lows, closes)
            above_cloud = ich.get('above_cloud', False)
            below_cloud = ich.get('below_cloud', False)
            tk_bull = ich.get('tk_cross_bull', False)
            ich_score_val = ich.get('score', 0)

            trend_long.append(IndicatorScore(
                name='Ichimoku Cloud', category='Trend',
                score=ich_score_val if above_cloud else (4 if tk_bull else 0),
                max_score=12,
                triggered=above_cloud,
                details=(
                    'Price above Ichimoku cloud'
                    + (' | TK cross bullish' if tk_bull else '')
                    + (' | Chikou confirms' if ich.get('chikou_confirms') else '')
                ) if above_cloud else '',
            ))
            trend_short.append(IndicatorScore(
                name='Ichimoku Cloud', category='Trend',
                score=ich_score_val if below_cloud else 0,
                max_score=12,
                triggered=below_cloud,
                details='Price below Ichimoku cloud' if below_cloud else '',
            ))
        except Exception:
            pass


        # ================================================================
        # SECTION 4 — MOMENTUM  (max ~52 pts)
        # ================================================================

        mom_long: list[IndicatorScore] = []
        mom_short: list[IndicatorScore] = []

        # ── 4a. RSI ───────────────────────────────────────────────────────
        try:
            rsi_res = self._rsi_analysis(closes)
            rsi14 = rsi_res.get('rsi14_current', 50.0)
            oversold = rsi_res.get('is_oversold', False)
            overbought = rsi_res.get('is_overbought', False)
            bull_div = rsi_res.get('bullish_divergence', False)
            bear_div = rsi_res.get('bearish_divergence', False)

            mom_long.append(IndicatorScore(
                name='RSI', category='Momentum',
                score=rsi_res.get('score_long', 0), max_score=15,
                triggered=oversold or bull_div,
                details=(
                    f"RSI14: {rsi14:.1f}"
                    + (' — Oversold' if oversold else '')
                    + (' — Bullish divergence' if bull_div else '')
                ),
            ))
            mom_short.append(IndicatorScore(
                name='RSI', category='Momentum',
                score=rsi_res.get('score_short', 0), max_score=15,
                triggered=overbought or bear_div,
                details=(
                    f"RSI14: {rsi14:.1f}"
                    + (' — Overbought' if overbought else '')
                    + (' — Bearish divergence' if bear_div else '')
                ),
            ))
        except Exception:
            pass

        # ── 4b. MACD ──────────────────────────────────────────────────────
        try:
            macd_res = self._macd(closes)
            bull_cross = macd_res.get('bull_cross', False)
            bear_cross = macd_res.get('bear_cross', False)
            macd_bull_div = macd_res.get('bullish_divergence', False)
            macd_bear_div = macd_res.get('bearish_divergence', False)

            mom_long.append(IndicatorScore(
                name='MACD', category='Momentum',
                score=macd_res.get('score_long', 0), max_score=12,
                triggered=bull_cross or macd_bull_div,
                details=(
                    'MACD bullish crossover' if bull_cross else
                    ('MACD bullish divergence' if macd_bull_div else '')
                ),
            ))
            mom_short.append(IndicatorScore(
                name='MACD', category='Momentum',
                score=macd_res.get('score_short', 0), max_score=12,
                triggered=bear_cross or macd_bear_div,
                details=(
                    'MACD bearish crossover' if bear_cross else
                    ('MACD bearish divergence' if macd_bear_div else '')
                ),
            ))
        except Exception:
            pass


        # ── 4f. Money Flow Index ─────────────────────────────────────────
        try:
            mfi_res = self._mfi(highs, lows, closes, volumes)
            mfi_val = mfi_res.get('current', 50.0)
            mfi_os = mfi_res.get('is_oversold', False)
            mfi_ob = mfi_res.get('is_overbought', False)

            mom_long.append(IndicatorScore(
                name='Money Flow Index', category='Momentum',
                score=mfi_res.get('score_long', 0), max_score=6,
                triggered=mfi_os,
                details=f"MFI: {mfi_val:.1f}" + (' — Oversold (money flowing in)' if mfi_os else ''),
            ))
            mom_short.append(IndicatorScore(
                name='Money Flow Index', category='Momentum',
                score=mfi_res.get('score_short', 0), max_score=6,
                triggered=mfi_ob,
                details=f"MFI: {mfi_val:.1f}" + (' — Overbought (money flowing out)' if mfi_ob else ''),
            ))
        except Exception:
            pass

        # ================================================================
        # SECTION 5 — VOLATILITY  (max ~34 pts)
        # ================================================================

        vol_long: list[IndicatorScore] = []
        vol_short: list[IndicatorScore] = []

        # ── 5a. Bollinger Bands ──────────────────────────────────────────
        try:
            bb = self._bollinger_bands(closes)
            pct_b = bb.get('percent_b_current', 0.5)
            below_lower = bb.get('below_lower', False)
            above_upper = bb.get('above_upper', False)
            squeeze_rel = bb.get('squeeze_released', False)

            vol_long.append(IndicatorScore(
                name='Bollinger Bands', category='Volatility',
                score=bb.get('score_long', 0), max_score=12,
                triggered=below_lower,
                details=(
                    f"BB %B: {pct_b:.2f}"
                    + (' — Below lower band' if below_lower else '')
                    + (' — Squeeze released' if squeeze_rel else '')
                ),
            ))
            vol_short.append(IndicatorScore(
                name='Bollinger Bands', category='Volatility',
                score=bb.get('score_short', 0), max_score=12,
                triggered=above_upper,
                details=(
                    f"BB %B: {pct_b:.2f}"
                    + (' — Above upper band' if above_upper else '')
                    + (' — Squeeze released' if squeeze_rel else '')
                ),
            ))
        except Exception:
            pass

        # ── 5b. Keltner Channel Squeeze ──────────────────────────────────
        try:
            kc = self._keltner_channels(highs, lows, closes)
            kc_squeeze = kc.get('squeeze_released', False)
            kc_score = kc.get('score', 0) if kc_squeeze else 0

            vol_long.append(IndicatorScore(
                name='Keltner Squeeze', category='Volatility',
                score=kc_score, max_score=10,
                triggered=kc_squeeze,
                details='BB/KC squeeze released — breakout imminent' if kc_squeeze else '',
            ))
            vol_short.append(IndicatorScore(
                name='Keltner Squeeze', category='Volatility',
                score=kc_score, max_score=10,
                triggered=kc_squeeze,
                details='BB/KC squeeze released' if kc_squeeze else '',
            ))
        except Exception:
            pass


        # ── 5d. ATR Volatility (also used for trade levels) ──────────────
        atr_result: dict = {}
        try:
            atr_result = self._atr_analysis(
                highs, lows, closes, float(closes[-1]), 'LONG'
            )
            high_vol = atr_result.get('is_high_volatility', False)
            atr_val = atr_result.get('atr', 0.0)
            atr_pct = atr_result.get('atr_pct', 0.0)
            atr_score = 5 if high_vol else 0

            vol_long.append(IndicatorScore(
                name='ATR Volatility', category='Volatility',
                score=atr_score, max_score=5,
                triggered=high_vol,
                details=f"ATR: {atr_val:.4f} ({atr_pct:.2f}% of price)"
                        + (' — Elevated volatility' if high_vol else ''),
            ))
            vol_short.append(IndicatorScore(
                name='ATR Volatility', category='Volatility',
                score=atr_score, max_score=5,
                triggered=high_vol,
                details=f"ATR: {atr_val:.4f} ({atr_pct:.2f}% of price)",
            ))
        except Exception:
            pass

        # ================================================================
        # SECTION 6 — VOLUME  (max ~31 pts)
        # ================================================================

        volume_long: list[IndicatorScore] = []
        volume_short: list[IndicatorScore] = []

        # ── 6a. Volume Spike ─────────────────────────────────────────────
        try:
            vs = self._volume_spike(volumes)
            spike = vs.get('is_spike', False)
            strength = vs.get('spike_strength', 1.0)

            volume_long.append(IndicatorScore(
                name='Volume Spike', category='Volume',
                score=vs.get('score', 0), max_score=12,
                triggered=spike,
                details=f"Volume: {strength:.1f}× average" + (' — Spike' if spike else ''),
            ))
            volume_short.append(IndicatorScore(
                name='Volume Spike', category='Volume',
                score=vs.get('score', 0), max_score=12,
                triggered=spike,
                details=f"Volume: {strength:.1f}× average" + (' — Spike' if spike else ''),
            ))
        except Exception:
            pass


        # ── 6c. VWAP ─────────────────────────────────────────────────────
        try:
            vwap_res = self._vwap(highs, lows, closes, volumes)
            crossed_above = vwap_res.get('crossed_above', False)
            crossed_below = vwap_res.get('crossed_below', False)
            bounce = vwap_res.get('bounce_at_vwap', False)
            pvwap = vwap_res.get('price_vs_vwap', 'neutral')

            volume_long.append(IndicatorScore(
                name='VWAP', category='Volume',
                score=vwap_res.get('score_long', 0), max_score=8,
                triggered=crossed_above or bounce,
                details=(
                    'Price crossed above VWAP' if crossed_above else
                    ('VWAP bounce — bullish' if bounce else f"Price {pvwap} VWAP")
                ),
            ))
            volume_short.append(IndicatorScore(
                name='VWAP', category='Volume',
                score=vwap_res.get('score_short', 0), max_score=8,
                triggered=crossed_below,
                details=(
                    'Price crossed below VWAP' if crossed_below
                    else f"Price {pvwap} VWAP"
                ),
            ))
        except Exception:
            pass


        # ================================================================
        # SECTION 7 — FIBONACCI  (max ~10 pts)
        # ================================================================

        fib_long: list[IndicatorScore] = []
        fib_short: list[IndicatorScore] = []

        try:
            fib_res = self._find_fib_zone(highs, lows, closes)
            at_ote = fib_res.get('at_ote_zone', False)
            fib_ratio = fib_res.get('current_ratio', None)
            ratio_str = f"Fib level: {fib_ratio:.3f}" if fib_ratio is not None else ''

            fib_long.append(IndicatorScore(
                name='Fibonacci OTE', category='Fibonacci',
                score=fib_res.get('score_long', 0), max_score=10,
                triggered=at_ote and fib_res.get('direction', '') == 'bullish',
                details=ratio_str + (' — In bullish OTE zone' if at_ote else ''),
            ))
            fib_short.append(IndicatorScore(
                name='Fibonacci OTE', category='Fibonacci',
                score=fib_res.get('score_short', 0), max_score=10,
                triggered=at_ote and fib_res.get('direction', '') == 'bearish',
                details=ratio_str + (' — In bearish OTE zone' if at_ote else ''),
            ))
        except Exception:
            pass

        # ================================================================
        # AGGREGATE — build final SignalScore objects
        # ================================================================

        def build_score(
            direction: str,
            ict: list[IndicatorScore],
            struct: list[IndicatorScore],
            trend_ind: list[IndicatorScore],
            mom: list[IndicatorScore],
            vol_s: list[IndicatorScore],
            volume_s: list[IndicatorScore],
            fib: list[IndicatorScore],
            atr_res: dict,
        ) -> SignalScore:
            all_scores = ict + struct + trend_ind + mom + vol_s + volume_s + fib
            raw = sum(s.score for s in all_scores)
            max_poss = sum(s.max_score for s in all_scores)
            confidence = normalize_score(raw, max_poss)
            band = score_to_confidence_band(confidence)

            # Top confluences: triggered, sorted by score descending, top-8
            triggered = [s for s in all_scores if s.triggered and s.score > 0]
            triggered.sort(key=lambda x: x.score, reverse=True)
            top_c = [
                f"{s.name}: {s.details}" if s.details else s.name
                for s in triggered[:8]
            ]

            # ── Trade level computation ─────────────────────────────────
            entry = float(closes[-1])

            if direction == 'LONG':
                sl = atr_res.get('stop_loss', entry * 0.985)
                tp1 = atr_res.get('take_profit_1', entry * 1.020)
                tp2 = atr_res.get('take_profit_2', entry * 1.035)
                tp3 = atr_res.get('take_profit_3', entry * 1.050)
            else:
                # Re-run ATR for short direction to get correct levels
                try:
                    from ..indicators.volatility import atr_analysis as _atr_fn
                    short_atr = _atr_fn(highs, lows, closes, entry, 'SHORT')
                    sl = short_atr.get('stop_loss', entry * 1.015)
                    tp1 = short_atr.get('take_profit_1', entry * 0.980)
                    tp2 = short_atr.get('take_profit_2', entry * 0.965)
                    tp3 = short_atr.get('take_profit_3', entry * 0.950)
                except Exception:
                    sl = entry * 1.015
                    tp1 = entry * 0.980
                    tp2 = entry * 0.965
                    tp3 = entry * 0.950

            risk = abs(entry - sl)
            rr = abs(tp2 - entry) / risk if risk > 0 else 0.0

            return SignalScore(
                direction=direction,
                raw_score=raw,
                max_possible=max_poss,
                confidence=confidence,
                confidence_band=band,
                ict_scores=ict,
                structure_scores=struct,
                trend_scores=trend_ind,
                momentum_scores=mom,
                volatility_scores=vol_s,
                volume_scores=volume_s,
                fibonacci_scores=fib,
                ict_zones=ict_zones,
                top_confluences=top_c,
                entry=round(entry, 8),
                stop_loss=round(sl, 8),
                take_profit_1=round(tp1, 8),
                take_profit_2=round(tp2, 8),
                take_profit_3=round(tp3, 8),
                rr_ratio=round(rr, 2),
            )

        long_signal = build_score(
            'LONG',
            ict_long, struct_long, trend_long, mom_long,
            vol_long, volume_long, fib_long,
            atr_result,
        )
        short_signal = build_score(
            'SHORT',
            ict_short, struct_short, trend_short, mom_short,
            vol_short, volume_short, fib_short,
            atr_result,
        )

        return long_signal, short_signal

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _empty_score(self, direction: str) -> SignalScore:
        """Return a zero-scored SignalScore for when we lack sufficient data."""
        return SignalScore(
            direction=direction,
            raw_score=0,
            max_possible=0,
            confidence=0,
            confidence_band='NO_SIGNAL',
        )
