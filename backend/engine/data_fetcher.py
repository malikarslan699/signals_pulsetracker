from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Callable, Optional

import aiohttp
from loguru import logger

from engine.candle_utils import Candle, normalize_binance_candle


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_BINANCE_INTERVAL_MAP: dict[str, str] = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "2H": "2h",
    "4H": "4h",
    "6H": "6h",
    "8H": "8h",
    "12H": "12h",
    "1D": "1d",
    "1W": "1w",
}

_TWELVEDATA_INTERVAL_MAP: dict[str, str] = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1H": "1h",
    "4H": "4h",
    "1D": "1day",
    "1W": "1week",
}


# ---------------------------------------------------------------------------
# BinanceDataFetcher
# ---------------------------------------------------------------------------
class BinanceDataFetcher:
    """
    Fetches historical candle data from Binance Futures REST API.

    Handles rate limits automatically (sliding window 1200 req/min weight).
    Retries on 429 / 5xx with exponential backoff.
    """

    BASE_URL = "https://fapi.binance.com"
    _MAX_WEIGHT_PER_MINUTE = 1200
    _KLINES_ENDPOINT = "/fapi/v1/klines"
    _EXCHANGE_INFO_ENDPOINT = "/fapi/v1/exchangeInfo"
    _TICKER_PRICE_ENDPOINT = "/fapi/v1/ticker/price"
    _FUNDING_RATE_ENDPOINT = "/fapi/v1/fundingRate"

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._session = session
        self._owns_session = session is None
        # Rate-limit state
        self._request_timestamps: list[float] = []
        self._request_lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "X-MBX-APIKEY": self._api_key,
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def _rate_limit_wait(self, weight: int = 1) -> None:
        """
        Enforce the Binance 1200 req/min rate limit using a sliding window.
        Sleeps if adding `weight` would exceed the limit.
        """
        async with self._request_lock:
            now = time.monotonic()
            # Prune timestamps older than 60 seconds
            self._request_timestamps = [
                t for t in self._request_timestamps if now - t < 60.0
            ]
            current_weight = len(self._request_timestamps)
            if current_weight + weight > self._MAX_WEIGHT_PER_MINUTE:
                oldest = self._request_timestamps[0] if self._request_timestamps else now
                sleep_for = 60.0 - (now - oldest) + 0.1
                if sleep_for > 0:
                    logger.debug(
                        f"Rate limit: sleeping {sleep_for:.1f}s (current weight={current_weight})"
                    )
                    await asyncio.sleep(sleep_for)
            for _ in range(weight):
                self._request_timestamps.append(time.monotonic())

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        max_retries: int = 5,
    ) -> Any:
        """
        Make an authenticated HTTP request with exponential backoff retry.
        """
        await self._rate_limit_wait()
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        delay = 1.0

        for attempt in range(max_retries):
            try:
                async with session.request(method, url, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", delay))
                        logger.warning(
                            f"Binance 429 on {endpoint}. Retry-After={retry_after}s."
                        )
                        await asyncio.sleep(retry_after)
                        delay = min(delay * 2, 60)
                    elif resp.status in (500, 502, 503, 504):
                        logger.warning(
                            f"Binance {resp.status} on {endpoint}. "
                            f"Attempt {attempt + 1}/{max_retries}."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, 30)
                    else:
                        body = await resp.text()
                        raise RuntimeError(
                            f"Binance API error {resp.status}: {body}"
                        )
            except aiohttp.ClientConnectorError as exc:
                logger.error(f"Connection error on {endpoint}: {exc}")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)

        raise RuntimeError(
            f"Binance API request to {endpoint} failed after {max_retries} retries."
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ) -> list[Candle]:
        """
        Fetch historical klines (OHLCV) from Binance Futures.

        Parameters
        ----------
        symbol   : str  — e.g. "BTCUSDT"
        interval : str  — internal timeframe key e.g. "1H", "4H", "1D"
        limit    : int  — number of candles (max 1500)
        """
        binance_interval = _BINANCE_INTERVAL_MAP.get(interval, interval.lower())
        limit = min(limit, 1500)

        params = {
            "symbol": symbol,
            "interval": binance_interval,
            "limit": limit,
        }
        raw: list = await self._request("GET", self._KLINES_ENDPOINT, params=params)
        return [normalize_binance_candle(k) for k in raw]

    async def get_exchange_info(self) -> dict:
        """Fetch full exchange info (all symbols, filters, precision)."""
        return await self._request("GET", self._EXCHANGE_INFO_ENDPOINT)

    async def get_active_futures_symbols(self) -> list[str]:
        """
        Return all TRADING perpetual USDT-margined futures symbols.
        """
        info = await self.get_exchange_info()
        symbols = [
            s["symbol"]
            for s in info.get("symbols", [])
            if s.get("status") == "TRADING"
            and s.get("contractType") == "PERPETUAL"
            and s.get("quoteAsset") == "USDT"
        ]
        return sorted(symbols)

    async def get_ticker_price(self, symbol: str) -> float:
        """Return the latest mark price for a symbol."""
        params = {"symbol": symbol}
        data = await self._request("GET", self._TICKER_PRICE_ENDPOINT, params=params)
        return float(data["price"])

    async def get_funding_rate(self, symbol: str) -> float:
        """Return the current funding rate for a perpetual futures symbol."""
        params = {"symbol": symbol, "limit": 1}
        data = await self._request("GET", self._FUNDING_RATE_ENDPOINT, params=params)
        if isinstance(data, list) and data:
            return float(data[0].get("fundingRate", 0.0))
        return 0.0


# ---------------------------------------------------------------------------
# BinanceWebSocketManager
# ---------------------------------------------------------------------------
class BinanceWebSocketManager:
    """
    Manages persistent WebSocket connections to Binance Futures Stream.

    Subscribes to combined kline streams for multiple symbols and timeframes.
    """

    _BASE_WS_URL = "wss://fstream.binance.com/stream"
    _MAX_STREAMS_PER_CONNECTION = 200
    _RECONNECT_DELAY_SECONDS = 3.0
    _MAX_RECONNECT_ATTEMPTS = 10

    def __init__(self) -> None:
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._session: Optional[aiohttp.ClientSession] = None

    async def subscribe_klines(
        self,
        symbols: list[str],
        timeframes: list[str],
        callback: Callable[[dict], None],
    ) -> None:
        """
        Subscribe to kline streams for a list of symbols and timeframes.

        Parameters
        ----------
        symbols    : list[str]  — e.g. ["BTCUSDT", "ETHUSDT"]
        timeframes : list[str]  — e.g. ["1H", "4H"]
        callback   : async callable — invoked with each closed kline dict
        """
        self._running = True

        # Build stream names: <symbol_lower>@kline_<interval>
        streams: list[str] = []
        for sym in symbols:
            for tf in timeframes:
                interval = _BINANCE_INTERVAL_MAP.get(tf, tf.lower())
                streams.append(f"{sym.lower()}@kline_{interval}")

        # Split into chunks (Binance limit = 200 streams per connection)
        chunks = [
            streams[i: i + self._MAX_STREAMS_PER_CONNECTION]
            for i in range(0, len(streams), self._MAX_STREAMS_PER_CONNECTION)
        ]

        for chunk in chunks:
            task = asyncio.create_task(
                self._listen(chunk, callback)
            )
            self._tasks.append(task)

        logger.info(
            f"Subscribed to {len(streams)} kline streams "
            f"across {len(chunks)} WebSocket connection(s)."
        )

    async def _listen(
        self,
        stream_names: list[str],
        callback: Callable[[dict], None],
    ) -> None:
        """Connect to a combined stream and forward closed klines to callback."""
        import websockets

        combined = "/".join(stream_names)
        url = f"{self._BASE_WS_URL}?streams={combined}"
        reconnect_attempts = 0

        while self._running:
            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                ) as ws:
                    reconnect_attempts = 0
                    logger.debug(
                        f"WebSocket connected: {len(stream_names)} streams."
                    )
                    async for raw_msg in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(raw_msg)
                            await self.on_kline_message(msg, callback)
                        except json.JSONDecodeError as exc:
                            logger.error(f"WS JSON decode error: {exc}")
                        except Exception as exc:
                            logger.error(f"WS message handling error: {exc}")

            except Exception as exc:
                if not self._running:
                    break
                reconnect_attempts += 1
                if reconnect_attempts > self._MAX_RECONNECT_ATTEMPTS:
                    logger.error(
                        "Max WebSocket reconnect attempts reached. Giving up."
                    )
                    break
                delay = min(
                    self._RECONNECT_DELAY_SECONDS * (2 ** (reconnect_attempts - 1)),
                    60.0,
                )
                logger.warning(
                    f"WS disconnected ({exc}). Reconnecting in {delay:.1f}s "
                    f"(attempt {reconnect_attempts}/{self._MAX_RECONNECT_ATTEMPTS})…"
                )
                await asyncio.sleep(delay)

    async def on_kline_message(
        self,
        msg: dict,
        callback: Callable[[dict], None],
    ) -> None:
        """
        Process a raw kline WebSocket message and invoke the callback
        for CLOSED candles only.

        Message format (combined stream):
        {
            "stream": "btcusdt@kline_1h",
            "data": {
                "e": "kline",
                "E": <event_time>,
                "s": "BTCUSDT",
                "k": {
                    "t": <open_time>, "o": ..., "h": ..., "l": ..., "c": ..., "v": ...,
                    "x": <is_closed>, ...
                }
            }
        }
        """
        data = msg.get("data", msg)  # handle both combined and single stream format
        kline = data.get("k", {})

        # Only forward closed (completed) candles
        if not kline.get("x", False):
            return

        symbol: str = data.get("s", "")
        # Map Binance interval back to our internal timeframe key
        binance_interval: str = kline.get("i", "")
        reverse_map = {v: k for k, v in _BINANCE_INTERVAL_MAP.items()}
        timeframe = reverse_map.get(binance_interval, binance_interval)

        candle: Candle = Candle(
            timestamp=int(kline["t"]),
            open=float(kline["o"]),
            high=float(kline["h"]),
            low=float(kline["l"]),
            close=float(kline["c"]),
            volume=float(kline["v"]),
        )

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candle": candle,
        }

        if asyncio.iscoroutinefunction(callback):
            await callback(payload)
        else:
            callback(payload)

    async def reconnect(self) -> None:
        """Gracefully restart all WebSocket connections."""
        logger.info("WebSocket manager reconnecting…")
        await self.stop()
        await asyncio.sleep(self._RECONNECT_DELAY_SECONDS)
        self._running = True

    async def stop(self) -> None:
        """Cancel all active WebSocket listener tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        logger.info("WebSocket manager stopped.")


# ---------------------------------------------------------------------------
# ForexDataFetcher
# ---------------------------------------------------------------------------
class ForexDataFetcher:
    """
    Fetches Forex, Commodity and Index candle data from TwelveData API.

    Supports: XAU/USD (Gold), WTI/USD (Oil), major forex pairs, indices.
    """

    _BASE_URL = "https://api.twelvedata.com"
    _TIMESERIES_ENDPOINT = "/time_series"

    # Map compact symbol names (used internally) → TwelveData symbol strings
    _SYMBOL_MAP: dict[str, str] = {
        # Metals / commodities
        'XAUUSD': 'XAU/USD',
        'XAGUSD': 'XAG/USD',
        'USOIL':  'WTI/USD',
        'UKOIL':  'BRENT/USD',
        # Indices
        'US100':  'NDX',
        'US500':  'SPX',
        'US30':   'DJI',
        'DE40':   'DAX',
        'UK100':  'FTSE',
        'JP225':  'N225',
    }

    def __init__(
        self,
        api_key: str = "",
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        import os
        # Fall back to environment variable if no key supplied directly
        self._api_key = api_key or os.getenv("TWELVEDATA_API_KEY", "")
        self._session = session
        self._owns_session = session is None

    @classmethod
    def _normalize_symbol(cls, symbol: str) -> str:
        """
        Convert compact symbol (e.g. 'EURUSD') to TwelveData format ('EUR/USD').
        Known mappings (metals, indices) are handled via _SYMBOL_MAP.
        For standard 6-char forex pairs not in the map, insert a slash: EURUSD→EUR/USD.
        """
        if symbol in cls._SYMBOL_MAP:
            return cls._SYMBOL_MAP[symbol]
        # Standard forex pair: 6 chars → split 3+3
        if len(symbol) == 6 and symbol.isalpha():
            return f"{symbol[:3]}/{symbol[3:]}"
        return symbol

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ) -> list[Candle]:
        """Alias for get_candles — provides a uniform interface with BinanceDataFetcher."""
        return await self.get_candles(symbol, interval, limit)

    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ) -> list[Candle]:
        """
        Fetch OHLCV candles from TwelveData.

        Parameters
        ----------
        symbol   : str — compact or TwelveData format, e.g. "EURUSD", "XAU/USD"
        interval : str — internal timeframe key (e.g. "1H", "4H")
        limit    : int — number of candles to retrieve (max 5000 per request)
        """
        symbol = self._normalize_symbol(symbol)
        td_interval = _TWELVEDATA_INTERVAL_MAP.get(interval, interval)
        limit = min(limit, 5000)

        params = {
            "symbol": symbol,
            "interval": td_interval,
            "outputsize": limit,
            "format": "JSON",
            "apikey": self._api_key,
        }

        session = await self._get_session()
        url = f"{self._BASE_URL}{self._TIMESERIES_ENDPOINT}"

        max_retries = 4
        delay = 2.0

        for attempt in range(max_retries):
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        if data.get("status") == "error":
                            code = data.get("code", 0)
                            message = data.get("message", "")
                            if code == 429:
                                logger.warning(
                                    f"TwelveData rate limit hit. Waiting {delay}s…"
                                )
                                await asyncio.sleep(delay)
                                delay = min(delay * 2, 60)
                                continue
                            raise RuntimeError(
                                f"TwelveData error [{code}]: {message}"
                            )

                        raw_candles = data.get("values", [])
                        candles: list[Candle] = []

                        for item in reversed(raw_candles):
                            # TwelveData provides datetime strings — convert to unix ms
                            dt_str = item.get("datetime", "")
                            ts_ms = _parse_twelvedata_datetime(dt_str)
                            candles.append(
                                Candle(
                                    timestamp=ts_ms,
                                    open=float(item["open"]),
                                    high=float(item["high"]),
                                    low=float(item["low"]),
                                    close=float(item["close"]),
                                    volume=float(item.get("volume", 0)),
                                )
                            )

                        return candles

                    elif resp.status == 429:
                        logger.warning(f"TwelveData 429. Waiting {delay}s…")
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, 60)
                    else:
                        body = await resp.text()
                        raise RuntimeError(
                            f"TwelveData HTTP {resp.status}: {body}"
                        )

            except aiohttp.ClientConnectorError as exc:
                logger.error(f"TwelveData connection error: {exc}")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)

        raise RuntimeError(
            f"TwelveData request for {symbol}/{interval} failed after "
            f"{max_retries} retries."
        )


def _parse_twelvedata_datetime(dt_str: str) -> int:
    """
    Parse a TwelveData datetime string to unix milliseconds.

    Supported formats:
        "2024-01-15 14:00:00"   — intraday
        "2024-01-15"            — daily/weekly
    """
    from datetime import datetime, timezone

    if not dt_str:
        return 0

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(dt_str, fmt)
            return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
        except ValueError:
            continue

    return 0
