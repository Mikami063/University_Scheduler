#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import time as time_mod
import os
import random
import unicodedata

TZ = ZoneInfo("America/Toronto")  # Ottawa

GREEN = "\033[32m"
RESET = "\033[0m"
HILITE = "\033[97;40m"
HILITE_RESET = "\033[0m"

# Sleep feature flag and config
SLEEP_ENABLED = False
SLEEP_START = time(22, 0)  # 10:00 PM
SLEEP_DURATION = timedelta(hours=10)

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
    # Monday (0)
    ClassEvent("CEG 4166", "Lecture",  "Learning Crossroads C442", 0, time(13, 0),  timedelta(minutes=80)),
    ClassEvent("CEG 4195", "Lecture",  "University Centre AUD",    0, time(14, 30), timedelta(minutes=80)),
    ClassEvent("CEG 4166", "Tutorial", "Henderson Residence 013",  0, time(17, 30), timedelta(minutes=80)),
    ClassEvent("MAT 2384", "Lecture",  "Learning Crossroads C140", 0, time(19, 0),  timedelta(minutes=80)),
    ClassEvent("MAT 2384", "Lecture",  "Learning Crossroads C140", 0, time(20, 30), timedelta(minutes=80)),  # screenshot shows 8:30–9:20, but keeping 80 per your rule

    # Tuesday (1)
    ClassEvent("CEG 4166", "Laboratory", "SITE 2061",              1, time(11, 30), timedelta(minutes=170)),
    ClassEvent("ECO 1102", "Lecture",    "Learning Crossroads C240",1, time(17, 30), timedelta(minutes=80)),

    # Wednesday (2)
    ClassEvent("CEG 4166", "Lecture",    "Learning Crossroads C442",2, time(11, 30), timedelta(minutes=80)),
    ClassEvent("CEG 4195", "Laboratory", "SITE 2060",              2, time(13, 0),  timedelta(minutes=170)),
    ClassEvent("MAT 2384", "Lecture",    "Tabaret Hall 333",       2, time(16, 0),  timedelta(minutes=80)),
    ClassEvent("ECO 1103", "Lecture",    "Tabaret Hall 333",       2, time(19, 0),  timedelta(minutes=170)),  # screenshot shows 7–10, but keeping 170 per your rule

    # Thursday (3)
    ClassEvent("CEG 4195", "Lecture",    "Henderson Residence 013", 3, time(16, 0),  timedelta(minutes=80)),
    ClassEvent("ECO 1102", "Lecture",    "Learning Crossroads C240",3, time(17, 30), timedelta(minutes=80)),
]

def build_sleep_events() -> list[ClassEvent]:
    if not SLEEP_ENABLED:
        return []
    events: list[ClassEvent] = []
    start_min = SLEEP_START.hour * 60 + SLEEP_START.minute
    duration_min = int(SLEEP_DURATION.total_seconds() // 60)
    for day in range(7):
        end_min = start_min + duration_min
        if end_min <= 24 * 60:
            events.append(ClassEvent("Sleep", "Rest", "Home", day, SLEEP_START, SLEEP_DURATION))
        else:
            first_duration = timedelta(minutes=(24 * 60 - start_min))
            second_duration = timedelta(minutes=(end_min - 24 * 60))
            events.append(ClassEvent("Sleep", "Rest", "Home", day, SLEEP_START, first_duration))
            next_day = (day + 1) % 7
            events.append(ClassEvent("Sleep", "Rest", "Home", next_day, time(0, 0), second_duration))
    return events

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

def display_width(text: str) -> int:
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width

def pad_to_width(text: str, width: int) -> str:
    pad = max(0, width - display_width(text))
    return text + (" " * pad)

def make_box(lines: list[str]) -> str:
    width = max(display_width(line) for line in lines)
    top = f"{GREEN}+{'-' * (width + 2)}+{RESET}"
    body = [f"{GREEN}| {RESET}{pad_to_width(line, width)}{GREEN} |{RESET}" for line in lines]
    bottom = f"{GREEN}+{'-' * (width + 2)}+{RESET}"
    return "\n".join([top, *body, bottom])

def ceil_to_step(value: int, step: int) -> int:
    if value % step == 0:
        return value
    return value + (step - (value % step))

def floor_to_step(value: int, step: int) -> int:
    return value - (value % step)

def build_weekly_view(now: datetime) -> str:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    slot_minutes = 30
    start_min, end_min = 0, 24 * 60
    now_minutes = now.hour * 60 + now.minute
    now_slot = floor_to_step(now_minutes, slot_minutes)

    all_events = SCHEDULE + build_sleep_events()
    labels = [f"{ev.course} {ev.kind}" for ev in all_events]
    col_width = max(12, *(display_width(label) for label in labels)) if labels else 12
    time_width = 6  # marker + HH:MM

    def cell(text: str, width: int) -> str:
        return pad_to_width(text[:width], width)

    def cell_hl(text: str, width: int, highlight: bool) -> str:
        content = cell(text, width)
        if not highlight:
            return content
        return f"{HILITE}{content}{HILITE_RESET}"

    line = "+" + "+".join(["-" * time_width] + ["-" * col_width] * len(days)) + "+"
    out: list[str] = [line]
    out.append("|" + "|".join([cell("Time", time_width)] + [cell(day, col_width) for day in days]) + "|")
    out.append(line)

    for t in range(start_min, end_min, slot_minutes):
        hh = t // 60
        mm = t % 60
        marker = "." if t == now_slot else " "
        row = [f"{marker}{hh:02d}:{mm:02d}"]
        for day_idx in range(7):
            label = ""
            for ev in all_events:
                if ev.weekday != day_idx:
                    continue
                ev_start = ev.start.hour * 60 + ev.start.minute
                ev_end = ev_start + int(ev.duration.total_seconds() // 60)
                if t == ev_start:
                    label = f"{ev.course} {ev.kind}"
                    break
                if ev_start < t < ev_end:
                    label = "|"
                    break
            if day_idx == now.weekday() and t == now_slot and not label:
                label = "."
            row.append(label)
        row_hl = t == now_slot
        out.append(
            "|"
            + "|".join(
                [cell_hl(row[0], time_width, row_hl)]
                + [
                    cell_hl(text, col_width, row_hl and day_idx == now.weekday())
                    for day_idx, text in enumerate(row[1:])
                ]
            )
            + "|"
        )
    out.append(line)
    return "\n".join(out)

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
                    "Current Class",
                    f"御課: {current_ev.course} {current_ev.kind}",
                    f"御室: {current_ev.room}",
                    f"終: {end_dt:%I:%M %p}",
                    f"御残時: {fmt_delta(remaining)}",
                    f"狐: {last_phrase_value}",
                ])
                print(box)
            else:
                print("No class in session.")
            print("")
            print("Weekly Schedule")
            print(build_weekly_view(now))
            time_mod.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
