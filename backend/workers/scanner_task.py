"""
Scanner Task — PulseSignal Pro

Scans all active trading pairs, runs indicator engine,
generates signals, stores in DB and Redis.
"""
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.celery_app import app
from loguru import logger


# ─── CRYPTO PAIRS (Top 100+ Binance Futures) ─────────────────────────────────
CRYPTO_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
    'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'NEARUSDT',
    'FTMUSDT', 'SANDUSDT', 'MANAUSDT', 'AXSUSDT', 'AAVEUSDT',
    'APTUSDT', 'OPUSDT', 'ARBUSDT', 'SUIUSDT', 'INJUSDT',
    'SEIUSDT', 'TIAUSDT', 'JUPUSDT', 'WIFUSDT', 'BONKUSDT',
    'PEPEUSDT', 'FLOKIUSDT', 'SHIBUSDT', 'GALAUSDT', 'APEUSDT',
    'COMPUSDT', 'MKRUSDT', 'SNXUSDT', 'CRVUSDT', 'YFIUSDT',
    'LDOUSDT', 'STETHUSDT', 'RPLUSDT', 'FXSUSDT', 'FRAXUSDT',
    '1000SHIBUSDT', '1000BONKUSDT', '1000PEPEUSDT', '1000FLOKIUSDT',
    'WBTCUSDT', 'HBARUSDT', 'ALGOUSDT', 'XTZUSDT', 'EOSUSDT',
    'ZECUSDT', 'DASHUSDT', 'XMRUSDT', 'BCHUSDT', 'ETCUSDT',
    'TRXUSDT', 'XLMUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT',
    'THETAUSDT', 'EGLDUSDT', 'FLOWUSDT', 'STXUSDT', 'CFXUSDT',
    'ENSUSDT', 'GMTUSDT', 'DYDXUSDT', 'GRTUSDT', 'COTIUSDT',
    'WOOUSDT', 'SPELLUSDT', 'ACHUSDT', 'IMXUSDT', 'LOOMUSDT',
    'CELOUSDT', 'ZRXUSDT', 'BANDUSDT', 'STORJUSDT', 'ANKRUSDT',
    'OCEANUSDT', 'FETUSDT', 'AGIXUSDT', 'RNDRUSDT', 'WLDUSDT',
    'CYBERUSDT', 'ARKMUSDT', 'PIXELUSDT', 'PORTALUSDT', 'STRAXUSDT',
    'BLURUSDT', 'NFPUSDT', 'AIUSDT', 'XAIUSDT', 'MANTAUSDT',
    'ALTUSDT', 'JUPUSDT', 'DYMUSDT', 'PYTHUSDT', 'STRKUSDT',
]

# ─── FOREX PAIRS ─────────────────────────────────────────────────────────────
FOREX_PAIRS = [
    'XAUUSD',   # Gold
    'XAGUSD',   # Silver
    'USOIL',    # WTI Crude Oil
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
    'EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY', 'CHFJPY',
    'EURCAD', 'EURAUD', 'GBPAUD', 'GBPCAD', 'AUDCAD', 'AUDNZD',
    'GBPNZD', 'EURNZD',
    'US100', 'US500', 'US30',  # Indices
    'DE40', 'UK100', 'JP225',
]

SCAN_TIMEFRAMES = ['5m', '15m', '1H', '4H']


def _json_default(value):
    """Convert common non-JSON-native numeric types (e.g. numpy scalars)."""
    try:
        import numpy as np  # local import to avoid hard dependency at module import
        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass

    if isinstance(value, (datetime,)):
        return value.isoformat()

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _run_async(coro):
    """Run async coroutine in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def _update_scanner_progress(signals_added: int = 0) -> None:
    """Increment scanner progress counters in Redis."""
    try:
        import redis

        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        status = (r.hget('scanner:status', 'status') or '').strip().lower()
        if status != 'running':
            return

        updated = r.hincrby('scanner:status', 'pairs_done', 1)
        if signals_added > 0:
            r.hincrby('scanner:status', 'signals_found', int(signals_added))

        total_raw = r.hget('scanner:status', 'pairs_total')
        try:
            total = int(total_raw or 0)
        except Exception:
            total = 0

        # Cap progress and mark run complete when all submitted pairs are done.
        if total > 0 and int(updated) > total:
            r.hset('scanner:status', mapping={'pairs_done': total})
            updated = total

        if total > 0 and int(updated) >= total:
            r.hset('scanner:status', mapping={
                'status': 'idle',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'is_running': 0,
            })
    except Exception:
        pass


async def _resolve_crypto_pairs() -> list[str]:
    """
    Keep scanner pairs aligned with currently tradeable Binance futures symbols.
    """
    try:
        from engine.data_fetcher import BinanceDataFetcher

        fetcher = BinanceDataFetcher()
        try:
            active_symbols = set(await fetcher.get_active_futures_symbols())
        finally:
            await fetcher.close()

        filtered = [symbol for symbol in CRYPTO_PAIRS if symbol in active_symbols]
        if filtered:
            return filtered
        if active_symbols:
            return sorted(active_symbols)
    except Exception as exc:
        logger.warning(f"[SCANNER] Could not refresh active Binance symbols: {exc}")
    return list(CRYPTO_PAIRS)


@app.task(bind=True, name='workers.scanner_task.scan_market',
          max_retries=2, default_retry_delay=60)
def scan_market(self, market: str = 'crypto'):
    """
    Main scanner task — runs every 10 minutes via Celery Beat.
    Scans all pairs for the given market.
    """
    logger.info(f"[SCANNER] Starting {market.upper()} scan...")
    start_time = time.time()

    if market == 'crypto':
        pairs = _run_async(_resolve_crypto_pairs())
    else:
        pairs = FOREX_PAIRS
    signals_found = 0
    errors = 0

    # Update scanner status in Redis
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.hset('scanner:status', mapping={
            'market': market,
            'status': 'running',
            'is_running': 1,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': '',
            'pairs_total': len(pairs),
            'pairs_done': 0,
            'signals_found': 0,
        })
    except Exception as e:
        logger.warning(f"Redis status update failed: {e}")

    # Process pairs in batches to avoid rate limits
    batch_size = 10
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i+batch_size]

        # Submit batch jobs
        for symbol in batch:
            try:
                scan_symbol.apply_async(
                    kwargs={'symbol': symbol, 'market': market},
                    queue='scanner',
                    countdown=0,
                )
            except Exception as e:
                logger.error(f"Failed to submit scan for {symbol}: {e}")
                errors += 1

        # Small delay between batches to avoid overwhelming the API
        time.sleep(0.5)

    duration = time.time() - start_time
    logger.info(f"[SCANNER] {market.upper()} scan submitted {len(pairs)} pairs in {duration:.1f}s")

    return {
        'market': market,
        'pairs_submitted': len(pairs),
        'errors': errors,
        'duration_ms': int(duration * 1000),
    }


@app.task(bind=True, name='workers.scanner_task.scan_symbol',
          max_retries=3, default_retry_delay=30)
def scan_symbol(self, symbol: str, market: str = 'crypto'):
    """
    Scan a single symbol across all timeframes.
    Generates signals and stores in DB/Redis.
    """
    try:
        result = _run_async(_scan_symbol_async(symbol, market))
        return result
    except Exception as exc:
        logger.error(f"Error scanning {symbol}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'symbol': symbol, 'error': str(exc), 'signals': 0}


async def _scan_symbol_async(symbol: str, market: str) -> dict:
    """Async implementation of symbol scanning"""
    signals_generated = []
    fetcher = None

    try:
        from engine.data_fetcher import BinanceDataFetcher, ForexDataFetcher
        from engine.signal_generator import SignalGenerator

        fetcher = BinanceDataFetcher() if market == 'crypto' else ForexDataFetcher()
        generator = SignalGenerator()

        # Fetch candles for all timeframes
        candles_by_tf = {}
        for tf in SCAN_TIMEFRAMES:
            try:
                candles = await fetcher.get_klines(symbol, tf, limit=200)
                if candles and len(candles) >= 50:
                    candles_by_tf[tf] = candles
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} {tf}: {e}")

        if not candles_by_tf:
            return {'symbol': symbol, 'market': market, 'signals': 0, 'error': 'No data'}

        # Cooldown TTL per timeframe — prevents re-firing the same
        # pair+direction+timeframe within the window (anti-spam).
        COOLDOWN_TTL: dict[str, int] = {
            '5m':  2700,    # 45 minutes
            '15m': 7200,    # 2 hours
            '1H':  21600,   # 6 hours
            '4H':  86400,   # 24 hours
            '1D':  172800,  # 48 hours
        }

        # Redis client for cooldown checks (sync, reused across TFs for this symbol)
        import redis as _redis_lib
        _r = _redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

        # Generate signals for each timeframe
        for tf, candles in candles_by_tf.items():
            try:
                signal = generator.generate(
                    symbol=symbol,
                    market=market,
                    candles=candles,
                    timeframe=tf,
                    candles_by_tf=candles_by_tf,
                )

                if signal:
                    # ── Anti-spam cooldown check ────────────────────────
                    # Skip if an identical direction+TF signal was recently fired
                    cooldown_key = f'signal:cooldown:{symbol}:{signal.direction}:{tf}'
                    if _r.exists(cooldown_key):
                        logger.debug(
                            f"[SCANNER] Cooldown active for {symbol} {signal.direction} {tf} — skipped"
                        )
                        continue

                    # Store in database and Redis
                    await _store_signal(signal)

                    # Set cooldown so the same signal can't fire again too soon
                    ttl = COOLDOWN_TTL.get(tf, 3600)
                    _r.set(cooldown_key, '1', ex=ttl)
                    signals_generated.append({
                        'direction': signal.direction,
                        'timeframe': signal.timeframe,
                        'confidence': signal.confidence,
                    })

                    # Trigger alert task
                    from workers.alert_task import send_signal_alerts
                    send_signal_alerts.apply_async(
                        kwargs={'signal_id': signal.id},
                        queue='alerts',
                        countdown=0,
                    )
            except Exception as e:
                logger.error(f"Error generating signal for {symbol} {tf}: {e}")

        # Cache candles in Redis for WS streaming
        try:
            import redis, json
            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            for tf, candles in candles_by_tf.items():
                key = f'candles:{symbol}:{tf}'
                # Store last 200 candles as JSON
                r.set(key, json.dumps(candles[-200:]), ex=3600)
        except Exception:
            pass

        return {
            'symbol': symbol,
            'market': market,
            'signals': len(signals_generated),
            'signal_details': signals_generated,
        }

    except Exception as e:
        logger.error(f"Async scan error for {symbol}: {e}")
        return {'symbol': symbol, 'market': market, 'signals': 0, 'error': str(e)}
    finally:
        _update_scanner_progress(signals_added=len(signals_generated))
        if fetcher is not None:
            try:
                await fetcher.close()
            except Exception:
                pass


async def _store_signal(signal) -> bool:
    """Store generated signal in PostgreSQL and Redis"""
    try:
        import json, redis as redis_lib
        from decimal import Decimal

        # Store in Redis for immediate access
        r = redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

        signal_dict = {
            'id': signal.id,
            'symbol': signal.symbol,
            'market': signal.market,
            'direction': signal.direction,
            'timeframe': signal.timeframe,
            'confidence': signal.confidence,
            'entry': signal.entry,
            'stop_loss': signal.stop_loss,
            'take_profit_1': signal.take_profit_1,
            'take_profit_2': signal.take_profit_2,
            'take_profit_3': signal.take_profit_3,
            'rr_ratio': signal.rr_ratio,
            'confidence_band': signal.confidence_band,
            'top_confluences': signal.top_confluences[:5],
            'fired_at': signal.fired_at,
        }

        # Store as latest signal for symbol
        signal_payload = json.dumps(signal_dict, default=_json_default)
        r.set(f'signal:latest:{signal.symbol}:{signal.timeframe}',
              signal_payload, ex=86400)

        # Add to active signals sorted set (score = confidence)
        r.zadd('signals:active', {signal_payload: signal.confidence})
        r.expire('signals:active', 86400)

        # New canonical cache keys used by API (/signals/live etc).
        r.set(f'signal:{signal.symbol}', signal_payload, ex=86400)
        r.zadd('active_signals', {signal.symbol: signal.confidence})
        r.expire('active_signals', 86400)

        # Publish for WebSocket broadcast
        r.publish('signals:live', signal_payload)

        # Store in PostgreSQL (using sync SQLAlchemy for Celery)
        try:
            from sqlalchemy import create_engine, text
            import json as json_lib
            from datetime import datetime as dt

            db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
            if db_url:
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    pair_row = conn.execute(
                        text("SELECT id FROM pairs WHERE symbol = :symbol LIMIT 1"),
                        {"symbol": signal.symbol},
                    ).mappings().first()
                    if not pair_row:
                        market = signal.market if signal.market in ("crypto", "forex") else (
                            "crypto" if signal.symbol.endswith("USDT") else "forex"
                        )
                        exchange = "binance" if market == "crypto" else "otc"
                        quote_asset = "USDT" if signal.symbol.endswith("USDT") else signal.symbol[-3:]
                        base_asset = signal.symbol[:-len(quote_asset)] if len(signal.symbol) > len(quote_asset) else signal.symbol

                        pair_row = conn.execute(
                            text(
                                """
                                INSERT INTO pairs (
                                    id, symbol, market, exchange, base_asset, quote_asset,
                                    is_active, precision_price, precision_qty, min_qty
                                ) VALUES (
                                    uuid_generate_v4(), :symbol, :market, :exchange, :base_asset, :quote_asset,
                                    true, 8, 3, 0.001
                                )
                                ON CONFLICT (symbol) DO UPDATE SET symbol = EXCLUDED.symbol
                                RETURNING id
                                """
                            ),
                            {
                                "symbol": signal.symbol,
                                "market": market,
                                "exchange": exchange,
                                "base_asset": base_asset,
                                "quote_asset": quote_asset,
                            },
                        ).mappings().first()
                        if not pair_row:
                            pair_row = conn.execute(
                                text("SELECT id FROM pairs WHERE symbol = :symbol LIMIT 1"),
                                {"symbol": signal.symbol},
                            ).mappings().first()
                        if not pair_row:
                            logger.warning(
                                f"DB store skipped for {signal.symbol}: unable to create/find pair id."
                            )
                            return True

                    expires_at = None
                    if getattr(signal, "expires_at", None):
                        try:
                            expires_at = dt.fromisoformat(
                                str(signal.expires_at).replace("Z", "+00:00")
                            )
                        except Exception:
                            expires_at = None

                    conn.execute(text("""
                        INSERT INTO signals (
                            id, pair_id, symbol, market, direction, timeframe, confidence,
                            entry, stop_loss, take_profit_1, take_profit_2, take_profit_3,
                            rr_ratio, raw_score, max_possible_score, status,
                            score_breakdown, ict_zones, mtf_analysis, candle_snapshot,
                            fired_at, expires_at, alert_sent
                        ) VALUES (
                            :id, :pair_id, :symbol, :market, :direction, :timeframe, :confidence,
                            :entry, :stop_loss, :tp1, :tp2, :tp3,
                            :rr, :raw_score, :max_score, 'active',
                            :breakdown, :ict_zones, :mtf, :snapshot,
                            :fired_at, :expires_at, false
                        )
                        ON CONFLICT (id) DO NOTHING
                    """), {
                        'id': signal.id,
                        'pair_id': pair_row["id"],
                        'symbol': signal.symbol,
                        'market': signal.market,
                        'direction': signal.direction,
                        'timeframe': signal.timeframe,
                        'confidence': signal.confidence,
                        'entry': signal.entry,
                        'stop_loss': signal.stop_loss,
                        'tp1': signal.take_profit_1,
                        'tp2': signal.take_profit_2,
                        'tp3': signal.take_profit_3,
                        'rr': signal.rr_ratio,
                        'raw_score': signal.raw_score,
                        'max_score': signal.max_possible_score,
                        'breakdown': json_lib.dumps(signal.score_breakdown, default=_json_default),
                        'ict_zones': json_lib.dumps(signal.ict_zones, default=_json_default),
                        'mtf': json_lib.dumps(signal.mtf_analysis, default=_json_default),
                        'snapshot': json_lib.dumps(signal.candle_snapshot, default=_json_default),
                        'fired_at': dt.fromisoformat(str(signal.fired_at).replace("Z", "+00:00")),
                        'expires_at': expires_at,
                    })
                    conn.commit()
        except Exception as db_err:
            logger.warning(f"DB store failed for {signal.symbol}: {db_err}")

        return True

    except Exception as e:
        logger.error(f"Store signal failed: {e}")
        return False


@app.task(name='workers.scanner_task.update_signal_statuses')
def update_signal_statuses():
    """
    Check active signals against current prices.
    Mark as TP1/TP2/TP3 hit or SL hit if applicable.
    """
    try:
        import redis, json
        import httpx

        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

        # Get all active signals from Redis
        active_raw = r.zrange('signals:active', 0, -1)

        for raw in active_raw:
            try:
                signal = json.loads(raw)
                symbol = signal.get('symbol')

                # Get current price
                try:
                    response = httpx.get(
                        f"https://fapi.binance.com/fapi/v1/ticker/price",
                        params={'symbol': symbol},
                        timeout=5
                    )
                    current_price = float(response.json().get('price', 0))
                except Exception:
                    continue

                if current_price <= 0:
                    continue

                direction = signal.get('direction')
                entry = float(signal.get('entry', 0))
                sl = float(signal.get('stop_loss', 0))
                tp1 = float(signal.get('take_profit_1', 0))
                tp2 = float(signal.get('take_profit_2', tp1))

                new_status = None

                if direction == 'LONG':
                    if current_price >= tp2:
                        new_status = 'tp2_hit'
                    elif current_price >= tp1:
                        new_status = 'tp1_hit'
                    elif current_price <= sl:
                        new_status = 'sl_hit'
                elif direction == 'SHORT':
                    if current_price <= tp2:
                        new_status = 'tp2_hit'
                    elif current_price <= tp1:
                        new_status = 'tp1_hit'
                    elif current_price >= sl:
                        new_status = 'sl_hit'

                # ── Expiry check ────────────────────────────────────────
                # If signal has passed its expires_at, mark as expired
                if not new_status:
                    expires_at_raw = signal.get('expires_at') or signal.get('fired_at')
                    try:
                        from datetime import datetime as _dt, timezone as _tz
                        expires_dt = _dt.fromisoformat(
                            str(expires_at_raw).replace('Z', '+00:00')
                        )
                        if expires_dt.tzinfo is None:
                            expires_dt = expires_dt.replace(tzinfo=_tz.utc)
                        if _dt.now(_tz.utc) > expires_dt:
                            new_status = 'expired'
                    except Exception:
                        pass

                if new_status:
                    # Update in DB
                    try:
                        from sqlalchemy import create_engine, text
                        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
                        if db_url:
                            engine = create_engine(db_url)
                            with engine.connect() as conn:
                                if new_status == 'expired':
                                    conn.execute(text("""
                                        UPDATE signals
                                        SET status = 'expired', closed_at = NOW()
                                        WHERE id = :id AND status = 'active'
                                    """), {'id': signal.get('id')})
                                else:
                                    pnl = ((current_price - entry) / entry * 100) if direction == 'LONG' else ((entry - current_price) / entry * 100)
                                    conn.execute(text("""
                                        UPDATE signals
                                        SET status = :status, close_price = :price,
                                            pnl_pct = :pnl, closed_at = NOW()
                                        WHERE id = :id AND status = 'active'
                                    """), {'status': new_status, 'price': current_price,
                                           'pnl': round(pnl, 2), 'id': signal.get('id')})
                                conn.commit()

                        # Remove from active signals
                        r.zrem('signals:active', raw)
                        r.zrem('active_signals', symbol)
                        r.delete(f'signal:{symbol}')

                        logger.info(f"Signal {signal.get('id')} -> {new_status} at {current_price}")
                    except Exception as e:
                        logger.error(f"Status update DB error: {e}")

            except Exception as e:
                logger.warning(f"Status check error: {e}")

    except Exception as e:
        logger.error(f"update_signal_statuses error: {e}")


@app.task(name='workers.scanner_task.health_check')
def health_check():
    """Ping task to verify workers are alive"""
    import redis
    try:
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.set('scanner:last_heartbeat', datetime.now(timezone.utc).isoformat(), ex=120)
        return {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
