"""
ICT Killzones — PulseSignal Pro

High-probability trading session times (UTC):
- Asian Session:        20:00 - 00:00  (setup session)
- London Open KZ:       02:00 - 05:00  (highest volume, big moves)
- New York Open KZ:     07:00 - 10:00  (highest probability)
- London Close KZ:      10:00 - 12:00  (reversal time)
- NY Lunch:             12:00 - 13:00  (low probability, avoid)
- NY Afternoon:         13:00 - 16:00  (late moves)
"""
from datetime import datetime, timezone, time, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class KillzoneResult:
    in_killzone: bool
    session_name: Optional[str]    # 'London Open', 'New York Open', etc.
    session_quality: str           # 'high', 'medium', 'low', 'avoid'
    score_bonus: int               # extra points if a signal fires during killzone
    time_to_next_kz: Optional[int] # minutes until next killzone
    next_kz_name: Optional[str]


# Ordered list for next-KZ calculation
KILLZONES: dict[str, dict] = {
    'Asian': {
        'start': time(20, 0),
        'end': time(0, 0),    # crosses midnight — handled specially
        'quality': 'medium',
        'score': 4,
        'description': 'Asian Session — Setup building',
    },
    'London Open': {
        'start': time(2, 0),
        'end': time(5, 0),
        'quality': 'high',
        'score': 8,
        'description': 'London Open Killzone — High probability',
    },
    'New York Open': {
        'start': time(7, 0),
        'end': time(10, 0),
        'quality': 'high',
        'score': 10,
        'description': 'NY Open Killzone — Highest probability',
    },
    'London Close': {
        'start': time(10, 0),
        'end': time(12, 0),
        'quality': 'high',
        'score': 7,
        'description': 'London Close — Reversal zone',
    },
    'NY Lunch': {
        'start': time(12, 0),
        'end': time(13, 0),
        'quality': 'avoid',
        'score': -5,
        'description': 'NY Lunch — Low volume, avoid',
    },
    'NY Afternoon': {
        'start': time(13, 0),
        'end': time(16, 0),
        'quality': 'medium',
        'score': 3,
        'description': 'NY Afternoon — Late session moves',
    },
}


def _time_in_zone(current: time, start: time, end: time) -> bool:
    """Check if current time falls within [start, end), handling midnight crossover."""
    if start == end:
        return False
    if start < end:
        return start <= current < end
    # Crosses midnight: e.g., 20:00 -> 00:00
    return current >= start or current < end


def _minutes_from_midnight(t: time) -> int:
    """Convert a time object to total minutes since midnight."""
    return t.hour * 60 + t.minute


def _get_next_killzone(current_time: time) -> tuple[str, int]:
    """
    Return (name, minutes_until_start) for the next upcoming killzone.
    Searches in UTC chronological order across a 24-hour window.
    """
    current_mins = _minutes_from_midnight(current_time)

    # Build a flat list of (start_minutes_mod_1440, name) sorted ascending
    candidates: list[tuple[int, str]] = []
    for name, kz in KILLZONES.items():
        start_mins = _minutes_from_midnight(kz['start'])
        candidates.append((start_mins, name))
    candidates.sort(key=lambda x: x[0])

    # Find the first start time strictly after current time (within 24h)
    for start_mins, name in candidates:
        if start_mins > current_mins:
            return name, start_mins - current_mins

    # All killzones have started earlier today — wrap around to tomorrow
    first_start, first_name = candidates[0]
    minutes_until = (24 * 60 - current_mins) + first_start
    return first_name, minutes_until


def is_in_killzone(dt: Optional[datetime] = None) -> KillzoneResult:
    """
    Check if the given datetime (UTC) falls within a killzone.

    If `dt` is None, uses the current UTC time.
    Returns a KillzoneResult describing the session and scoring bonus.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    current_time = dt.time().replace(tzinfo=None)   # naive UTC time

    for name, kz in KILLZONES.items():
        if _time_in_zone(current_time, kz['start'], kz['end']):
            # Already inside a killzone — compute time to next one
            next_kz_name, mins_to_next = _get_next_killzone(kz['end'])
            return KillzoneResult(
                in_killzone=True,
                session_name=name,
                session_quality=kz['quality'],
                score_bonus=kz['score'],
                time_to_next_kz=mins_to_next,
                next_kz_name=next_kz_name,
            )

    # Not in any killzone
    next_kz_name, mins_to_next = _get_next_killzone(current_time)
    return KillzoneResult(
        in_killzone=False,
        session_name=None,
        session_quality='low',
        score_bonus=0,
        time_to_next_kz=mins_to_next,
        next_kz_name=next_kz_name,
    )


def get_current_session(dt: Optional[datetime] = None) -> str:
    """Return the name of the current trading session, or 'Off-Hours'."""
    result = is_in_killzone(dt)
    return result.session_name or 'Off-Hours'


def get_session_score(dt: Optional[datetime] = None) -> int:
    """
    Return the session score bonus for signal weighting.
    Positive during high-probability sessions, negative during NY Lunch.
    """
    result = is_in_killzone(dt)
    return result.score_bonus


def get_all_killzone_times() -> dict[str, dict]:
    """
    Return all killzone definitions with their UTC start/end times.
    Useful for front-end rendering of session bands.
    """
    return {
        name: {
            'start': kz['start'].strftime('%H:%M'),
            'end': kz['end'].strftime('%H:%M'),
            'quality': kz['quality'],
            'score': kz['score'],
            'description': kz['description'],
        }
        for name, kz in KILLZONES.items()
    }


def is_optimal_entry_window(dt: Optional[datetime] = None) -> bool:
    """
    Returns True if current time is in a high-probability killzone
    (London Open, New York Open, or London Close) but NOT NY Lunch.
    """
    result = is_in_killzone(dt)
    return result.session_quality == 'high'
