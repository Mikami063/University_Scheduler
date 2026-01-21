#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import time as time_mod
import os

TZ = ZoneInfo("America/Toronto")  # Ottawa

# Monday=0 ... Sunday=6
@dataclass(frozen=True)
class ClassEvent:
    name: str
    weekday: int
    start: time

SCHEDULE: list[ClassEvent] = [
    # From your screenshot
    ClassEvent("CEG 4166 Lecture", 0, time(13, 0)),
    ClassEvent("CEG 4195 Lecture", 0, time(14, 30)),
    ClassEvent("CEG 4166 Tutorial", 0, time(17, 30)),
    ClassEvent("MAT 2384 Lecture", 0, time(19, 0)),
    ClassEvent("MAT 2384 Lecture", 0, time(20, 30)),

    ClassEvent("CEG 4166 Lab", 1, time(11, 30)),

    ClassEvent("CEG 4166 Lecture", 2, time(11, 30)),
    ClassEvent("CEG 4195 Lab", 2, time(13, 0)),
    ClassEvent("MAT 2384 Lecture", 2, time(16, 0)),

    ClassEvent("CEG 4195 Lecture", 3, time(16, 0)),
]

def next_occurrence(now: datetime, ev: ClassEvent) -> datetime:
    days_ahead = (ev.weekday - now.weekday()) % 7
    candidate_date = now.date() + timedelta(days=days_ahead)
    candidate = datetime.combine(candidate_date, ev.start, tzinfo=TZ)
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate

def fmt_delta(td: timedelta) -> str:
    total = int(td.total_seconds())
    if total < 0:
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def compute_next(now: datetime) -> tuple[datetime, ClassEvent, timedelta]:
    occ, ev = min(
        ((next_occurrence(now, ev), ev) for ev in SCHEDULE),
        key=lambda x: x[0]
    )
    return occ, ev, (occ - now)

def compute_departure_time(delta: timedelta) -> timedelta:
    # Assuming you want to leave 20 minutes before class starts
    return delta - timedelta(minutes=20)

def compute_lunch_time(delta: timedelta) -> timedelta:
    return delta - timedelta(minutes=45)

def main() -> None:
    try:
        while True:
            now = datetime.now(TZ)
            occ, ev, delta = compute_next(now)

            clear_screen()
            print(f"Now:        {now:%a %Y-%m-%d %H:%M:%S %Z}")
            print(f"Next class: {ev.name} @ {occ:%a %H:%M}")
            print(f"Time left:  {fmt_delta(delta)} (HH:MM:SS)")
            print(f"Departure:  {fmt_delta(compute_departure_time(delta))} (HH:MM:SS)")
            print(f"Departure with Lunch: {fmt_delta(compute_lunch_time(compute_departure_time(delta)))} (HH:MM:SS)")
            time_mod.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()