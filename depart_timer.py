#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import sys

TZ = ZoneInfo("America/Toronto")
DEPARTURE_LEAD = timedelta(minutes=20)

TIME_FORMATS = [
    "%H:%M",
    "%H:%M:%S",
    "%I:%M%p",
    "%I:%M %p",
    "%I:%M:%S%p",
    "%I:%M:%S %p",
]


def parse_time(value: str) -> time:
    cleaned = value.strip().upper()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).time()
        except ValueError:
            continue
    raise ValueError("Use HH:MM (24h) or H:MM AM/PM.")


def next_datetime_for_time(now: datetime, target: time) -> datetime:
    candidate = datetime.combine(now.date(), target, tzinfo=TZ)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def fmt_delta(td: timedelta) -> str:
    total = int(td.total_seconds())
    if total < 0:
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    raw = input("Enter target time (e.g. 14:30 or 2:30 PM): ")
    now = datetime.now(TZ)
    try:
        target_time = parse_time(raw)
    except ValueError as exc:
        print(f"Invalid time: {exc}")
        sys.exit(1)

    target_dt = next_datetime_for_time(now, target_time)
    depart_dt = target_dt - DEPARTURE_LEAD
    until_depart = depart_dt - now

    print(f"Now:           {now:%Y-%m-%d %I:%M:%S %p %Z}")
    print(f"Target time:   {target_dt:%Y-%m-%d %I:%M %p}")
    print(f"Depart time:   {depart_dt:%Y-%m-%d %I:%M %p}")
    if until_depart.total_seconds() <= 0:
        print("Time left:     00:00:00 (leave now)")
    else:
        print(f"Time left:     {fmt_delta(until_depart)} (HH:MM:SS)")


if __name__ == "__main__":
    main()
