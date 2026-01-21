#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import time as time_mod
import os
import random

TZ = ZoneInfo("America/Toronto")  # Ottawa

GREEN = "\033[32m"
RESET = "\033[0m"

# Monday=0 ... Sunday=6
@dataclass(frozen=True)
class ClassEvent:
    course: str
    kind: str
    room: str
    weekday: int
    start: time
    duration: timedelta

SCHEDULE: list[ClassEvent] = [
    # From your screenshot
    ClassEvent("CEG 4166", "Lecture", "TBD", 0, time(13, 0), timedelta(minutes=80)),
    ClassEvent("CEG 4195", "Lecture", "TBD", 0, time(14, 30), timedelta(minutes=80)),
    ClassEvent("CEG 4166", "Tutorial", "TBD", 0, time(17, 30), timedelta(minutes=80)),
    ClassEvent("MAT 2384", "Lecture", "TBD", 0, time(19, 0), timedelta(minutes=80)),
    ClassEvent("MAT 2384", "Lecture", "TBD", 0, time(20, 30), timedelta(minutes=80)),

    ClassEvent("CEG 4166", "Lab", "TBD", 1, time(11, 30), timedelta(minutes=170)),

    ClassEvent("CEG 4166", "Lecture", "TBD", 2, time(11, 30), timedelta(minutes=80)),
    ClassEvent("CEG 4195", "Lab", "TBD", 2, time(13, 0), timedelta(minutes=170)),
    ClassEvent("MAT 2384", "Lecture", "TBD", 2, time(16, 0), timedelta(minutes=80)),

    ClassEvent("CEG 4195", "Lecture", "TBD", 3, time(16, 0), timedelta(minutes=80)),
]

PHRASES = {
    "beginning": [
        "Kyaa! System booting—I'm 3% caffeine and 97% chaos!",
        "Your attention is mine now. Focus mode: ON!",
        "Senpai, class has begun—don’t blink or I’ll steal your notes!",
        "Warm-up arc activated. Plot armor engaged!",
        "I tied my sanity into a bow. Let’s go!",
    ],
    "middle": [
        "Mid-class power spike! My brain is doing parkour!",
        "This lecture slaps. I’m the soundtrack.",
        "I’m taking notes so aggressively the pages are flinching.",
        "Focus so hard I can hear the chalk’s life story.",
        "We are deep in the academic dungeon. Loot = knowledge!",
    ],
    "end": [
        "Final stretch! I can taste freedom and it’s spicy.",
        "We’re in the outro—cue sparkles, cue victory scream!",
        "Endgame energy: I will not be defeated by time.",
        "Wrap-up mode: chaos contained, for now.",
        "Class ending! Release the gremlin!",
    ],
}


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

def class_end(start_dt: datetime, ev: ClassEvent) -> datetime:
    return start_dt + ev.duration

def compute_current(now: datetime) -> tuple[datetime, ClassEvent, timedelta] | None:
    today = now.date()
    candidates: list[tuple[datetime, ClassEvent]] = []
    for ev in SCHEDULE:
        if ev.weekday != now.weekday():
            continue
        start_dt = datetime.combine(today, ev.start, tzinfo=TZ)
        end_dt = class_end(start_dt, ev)
        if start_dt <= now < end_dt:
            candidates.append((start_dt, ev))
    if not candidates:
        return None
    start_dt, ev = max(candidates, key=lambda x: x[0])
    return start_dt, ev, (class_end(start_dt, ev) - now)

def phrase_stage(start_dt: datetime, ev: ClassEvent, now: datetime) -> str:
    elapsed = (now - start_dt).total_seconds()
    total = ev.duration.total_seconds()
    if total <= 0:
        return "middle"
    progress = max(0.0, min(1.0, elapsed / total))
    if progress < 1 / 3:
        return "beginning"
    if progress < 2 / 3:
        return "middle"
    return "end"

def make_box(lines: list[str]) -> str:
    width = max(len(line) for line in lines)
    top = f"{GREEN}+{'-' * (width + 2)}+{RESET}"
    body = [f"{GREEN}| {RESET}{line.ljust(width)}{GREEN} |{RESET}" for line in lines]
    bottom = f"{GREEN}+{'-' * (width + 2)}+{RESET}"
    return "\n".join([top, *body, bottom])

def compute_departure_time(delta: timedelta) -> timedelta:
    # Assuming you want to leave 20 minutes before class starts
    return delta - timedelta(minutes=20)

def compute_lunch_time(delta: timedelta) -> timedelta:
    return delta - timedelta(minutes=45)

def main() -> None:
    try:
        last_phrase_key: tuple[str, str] | None = None
        last_phrase_value = ""
        while True:
            now = datetime.now(TZ)
            current = compute_current(now)
            occ, ev, delta = compute_next(now)

            clear_screen()
            print(f"Now:        {now:%a %Y-%m-%d %I:%M:%S %p %Z}")
            print(f"Next class: {ev.course} {ev.kind} ({ev.room}) @ {occ:%a %I:%M %p}")
            print(f"Time left:  {fmt_delta(delta)} (HH:MM:SS)")
            print(f"Departure:  {fmt_delta(compute_departure_time(delta))} (HH:MM:SS)")
            print(f"Departure with Lunch: {fmt_delta(compute_lunch_time(compute_departure_time(delta)))} (HH:MM:SS)")
            print("")

            if current:
                start_dt, current_ev, remaining = current
                stage = phrase_stage(start_dt, current_ev, now)
                phrase_key = (f"{current_ev.course}-{current_ev.kind}", stage)
                if phrase_key != last_phrase_key:
                    last_phrase_value = random.choice(PHRASES[stage])
                    last_phrase_key = phrase_key
                end_dt = class_end(start_dt, current_ev)
                box = make_box([
                    "Current class",
                    f"Course: {current_ev.course} {current_ev.kind}",
                    f"Room: {current_ev.room}",
                    f"Ends at: {end_dt:%I:%M %p}",
                    f"Time left: {fmt_delta(remaining)}",
                    f"狐: {last_phrase_value}",
                ])
                print(box)
            else:
                print("No class in session.")
            time_mod.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
