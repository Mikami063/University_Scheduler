#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import time as time_mod
import os
import random
import unicodedata
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

TZ = ZoneInfo("America/Toronto")  # Ottawa

GREEN = "\033[32m"
RESET = "\033[0m"
HILITE = "\033[97;40m"
HILITE_RESET = "\033[0m"
FG_WHITE = "\033[97m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_YELLOW = "\033[43m"
BG_GREEN = "\033[42m"

# Sleep feature flag and config
SLEEP_ENABLED = True
SLEEP_START = time(23, 0)  # 10:00 PM
SLEEP_DURATION = timedelta(hours=9)
SLEEP_EVENT_COLOR = BG_CYAN
MORNING_ENABLED = True
MORNING_DURATION = timedelta(minutes=60)
MORNING_EVENT_COLOR = BG_YELLOW

# Monday=0 ... Sunday=6
@dataclass(frozen=True)
class ClassEvent:
    course: str
    kind: str
    room: str
    weekday: int
    start: time
    duration: timedelta
    color: str = ""

@dataclass(frozen=True)
class DueItem:
    title: str
    kind: str
    due_date: datetime

SCHEDULE: list[ClassEvent] = [
    # Monday (0)
    ClassEvent("CSI 2372", "Lecture",  "Tabaret Hall 333", 0, time(16, 0),  timedelta(minutes=80)),
    ClassEvent("CEG 4136", "Laboratory",  "Colonel By Hall B302",    0, time(19, 00), timedelta(minutes=170)),

    # Tuesday (1)
    ClassEvent("CSI 2372", "Laboratory", "SITE 2060",              1, time(8, 30), timedelta(minutes=80)),
    ClassEvent("JPN 3901", "Lecture", "Simard Hall 427",              1, time(17, 30), timedelta(minutes=80)),
    ClassEvent("CSI 2372", "Tutorial", "Simard Hall 425",              1, time(19, 00), timedelta(minutes=80)),

    # Wednesday (2)
    ClassEvent("CEG 4912", "Lecture",    "***",2, time(10, 00), timedelta(minutes=80)),
    ClassEvent("CEG 4136", "Lecture", "Social Science Building 1007",              2, time(13, 0),  timedelta(minutes=80)),
    ClassEvent("CSI 2372", "Lecture",    "Tabaret Hall 333",       2, time(14, 30),  timedelta(minutes=80)),

    # Thursday (3)
    ClassEvent("CEG 4912", "Laboratory", "SITE 2061",              3, time(10, 00), timedelta(minutes=170)),
    ClassEvent("JPN 3901", "Lecture", "Simard Hall 427",              3, time(17, 30), timedelta(minutes=80)),

    # Friday (4)
    ClassEvent("CEG 4912", "Laboratory", "SITE 2061",              4, time(8, 30), timedelta(minutes=170)),
    ClassEvent("CEG 4136", "Lecture", "Hagen Hall 302",              4, time(11, 30),  timedelta(minutes=80)),
    ClassEvent("CEG 4136", "Tutorial", "Hagen Hall 302",              4, time(13, 00),  timedelta(minutes=80)),
        
]

PERSONAL_SCHEDULE: list[ClassEvent] = [
    
]

CLASS_EVENT_COLOR = BG_BLUE
PERSONAL_EVENT_COLOR = BG_MAGENTA
FOOD_EVENT_COLOR = BG_GREEN

FOOD_SCHEDULE: list[ClassEvent] = [

]

DUE_ITEMS: list[DueItem] = [
    
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
            events.append(ClassEvent("Sleep", "Rest", "Home", day, SLEEP_START, SLEEP_DURATION, SLEEP_EVENT_COLOR))
        else:
            first_duration = timedelta(minutes=(24 * 60 - start_min))
            second_duration = timedelta(minutes=(end_min - 24 * 60))
            events.append(ClassEvent("Sleep", "Rest", "Home", day, SLEEP_START, first_duration, SLEEP_EVENT_COLOR))
            next_day = (day + 1) % 7
            events.append(ClassEvent("Sleep", "Rest", "Home", next_day, time(0, 0), second_duration, SLEEP_EVENT_COLOR))
    return events

def build_morning_events() -> list[ClassEvent]:
    if not (SLEEP_ENABLED and MORNING_ENABLED):
        return []
    events: list[ClassEvent] = []
    start_min = SLEEP_START.hour * 60 + SLEEP_START.minute
    sleep_min = int(SLEEP_DURATION.total_seconds() // 60)
    routine_min = int(MORNING_DURATION.total_seconds() // 60)
    for day in range(7):
        sleep_end_min = start_min + sleep_min
        end_day = day
        if sleep_end_min >= 24 * 60:
            sleep_end_min -= 24 * 60
            end_day = (day + 1) % 7
        routine_end_min = sleep_end_min + routine_min
        if routine_end_min <= 24 * 60:
            events.append(
                ClassEvent(
                    "Morning",
                    "Routine",
                    "Home",
                    end_day,
                    time(sleep_end_min // 60, sleep_end_min % 60),
                    timedelta(minutes=routine_min),
                    MORNING_EVENT_COLOR,
                )
            )
        else:
            first_duration = timedelta(minutes=(24 * 60 - sleep_end_min))
            second_duration = timedelta(minutes=(routine_end_min - 24 * 60))
            events.append(
                ClassEvent(
                    "Morning",
                    "Routine",
                    "Home",
                    end_day,
                    time(sleep_end_min // 60, sleep_end_min % 60),
                    first_duration,
                    MORNING_EVENT_COLOR,
                )
            )
            next_day = (end_day + 1) % 7
            events.append(
                ClassEvent(
                    "Morning",
                    "Routine",
                    "Home",
                    next_day,
                    time(0, 0),
                    second_duration,
                    MORNING_EVENT_COLOR,
                )
            )
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

def fmt_delta_hm(td: timedelta) -> str:
    total = int(td.total_seconds())
    if total < 0:
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    return f"{h:02d}:{m:02d}"

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
    sleep_window = current_sleep_window(now)
    sleep_marker_day: int | None = None
    sleep_marker_slot: int | None = None
    sleep_marker_label = ""
    if sleep_window:
        _, sleep_end = sleep_window
        if sleep_end > now:
            mid_dt = now + (sleep_end - now) / 2
            sleep_marker_day = mid_dt.weekday()
            mid_minutes = mid_dt.hour * 60 + mid_dt.minute
            sleep_marker_slot = floor_to_step(mid_minutes, slot_minutes)
            sleep_marker_label = f"|Wake in: {fmt_delta(sleep_end - now)}"

    sleep_events = build_sleep_events()
    morning_events = build_morning_events()
    # Higher priority renders on top when events overlap.
    event_sources = (
        [(ev, ev.color or PERSONAL_EVENT_COLOR, 3) for ev in PERSONAL_SCHEDULE]
        + [(ev, ev.color or FOOD_EVENT_COLOR, 2) for ev in FOOD_SCHEDULE]
        + [(ev, ev.color or CLASS_EVENT_COLOR, 1) for ev in SCHEDULE]
        + [(ev, ev.color, 0) for ev in sleep_events]
        + [(ev, ev.color, 0) for ev in morning_events]
    )
    labels = [f"{ev.course} {ev.kind}" for ev, _, _ in event_sources]
    col_width = max(12, *(display_width(label) for label in labels)) if labels else 12
    time_width = 6  # marker + HH:MM

    def cell(text: str, width: int) -> str:
        return pad_to_width(text[:width], width)

    def cell_hl(text: str, width: int, highlight: bool) -> str:
        content = cell(text, width)
        if not highlight:
            return content
        return f"{HILITE}{content}{HILITE_RESET}"

    def cell_color(text: str, width: int, color: str) -> str:
        content = cell(text, width)
        if not color:
            return content
        return f"{FG_WHITE}{color}{content}{RESET}"

    line = "+" + "+".join(["-" * time_width] + ["-" * col_width] * len(days)) + "+"
    out: list[str] = [line]
    out.append("|" + "|".join([cell("Time", time_width)] + [cell(day, col_width) for day in days]) + "|")
    out.append(line)

    for t in range(start_min, end_min, slot_minutes):
        hh = t // 60
        mm = t % 60
        marker = "." if t == now_slot else " "
        row = [f"{marker}{hh:02d}:{mm:02d}"]
        row_colors: list[str] = []
        for day_idx in range(7):
            label = ""
            color = ""
            matches: list[tuple[int, str, str, bool, ClassEvent]] = []
            for ev, default_color, priority in event_sources:
                if ev.weekday != day_idx:
                    continue
                ev_start = ev.start.hour * 60 + ev.start.minute
                ev_end = ev_start + int(ev.duration.total_seconds() // 60)
                if ev.course == "Sleep" and ev.kind == "Rest":
                    start_slot = floor_to_step(ev_start, slot_minutes)
                    end_slot = ceil_to_step(ev_end, slot_minutes)
                    last_slot = max(start_slot, end_slot - slot_minutes)
                    if t == start_slot:
                        matches.append((priority, "Sleep", default_color, True, ev))
                    elif t == last_slot:
                        matches.append((priority, "E", default_color, False, ev))
                    elif start_slot < t < end_slot:
                        matches.append((priority, "|", default_color, False, ev))
                else:
                    if t == ev_start:
                        matches.append((priority, f"{ev.course} {ev.kind}", default_color, True, ev))
                    if ev_start < t < ev_end:
                        matches.append((priority, "|", default_color, False, ev))
            if matches:
                # Pick highest-priority event; mark overlaps.
                priority, label, color, is_start, _ = max(matches, key=lambda x: x[0])
                if len(matches) > 1:
                    label = (label + " +") if is_start else "|+"
            if (
                sleep_marker_day is not None
                and sleep_marker_slot is not None
                and day_idx == sleep_marker_day
                and t == sleep_marker_slot
                and (not label or (label in ("Sleep", "|", "E") and color == SLEEP_EVENT_COLOR))
            ):
                label = sleep_marker_label
                color = SLEEP_EVENT_COLOR
            if day_idx == now.weekday() and t == now_slot and not label:
                label = "."
            row.append(label)
            row_colors.append(color)
        row_hl = t == now_slot
        out.append(
            "|"
            + "|".join(
                [cell_hl(row[0], time_width, row_hl)]
                + [
                    cell_hl(text, col_width, row_hl and day_idx == now.weekday())
                    if row_hl and day_idx == now.weekday()
                    else (cell_color(text, col_width, color) if text else cell(text, col_width))
                    for day_idx, (text, color) in enumerate(zip(row[1:], row_colors))
                ]
            )
            + "|"
        )
    out.append(line)
    return "\n".join(out)

def build_due_view(now: datetime) -> str:
    week_start = now.date() - timedelta(days=now.weekday())
    today = now.date()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weeks = [week_start, week_start + timedelta(days=7)]

    def day_label(d) -> str:
        return f"{d:%m/%d}"

    due_map: dict[datetime.date, list[str]] = {}
    for item in DUE_ITEMS:
        d = item.due_date.date()
        if week_start <= d <= (week_start + timedelta(days=13)):
            due_map.setdefault(d, []).append(f"{item.title} ({item.kind})")

    col_width = 18
    line = "+" + "+".join(["-" * col_width] * 7) + "+"

    def cell_hl(text: str, highlight: bool) -> str:
        content = pad_to_width(text[:col_width], col_width)
        if not highlight:
            return content
        return f"{HILITE}{content}{HILITE_RESET}"

    out: list[str] = []
    for w, start in enumerate(weeks):
        out.append("Due This Week" if w == 0 else "Due Next Week")
        out.append(line)
        out.append("|" + "|".join([pad_to_width(days[i], col_width) for i in range(7)]) + "|")
        out.append(
            "|"
            + "|".join([cell_hl(day_label(start + timedelta(days=i)), start + timedelta(days=i) == today) for i in range(7)])
            + "|"
        )
        out.append(line)
        max_rows = 3
        for r in range(max_rows):
            row_cells = []
            for i in range(7):
                d = start + timedelta(days=i)
                items = due_map.get(d, [])
                text = items[r] if r < len(items) else ""
                row_cells.append(pad_to_width(text[:col_width], col_width))
            out.append("|" + "|".join(row_cells) + "|")
        out.append(line)
    return "\n".join(out)

def build_due_list(now: datetime) -> str:
    if not DUE_ITEMS:
        return "No due items."
    items = sorted(DUE_ITEMS, key=lambda i: i.due_date)
    lines = ["All Tasks (days until due)"]
    for item in items:
        days_left = (item.due_date.date() - now.date()).days
        lines.append(f"{item.title} | {item.kind} | {days_left:+d}d | {item.due_date:%Y-%m-%d %I:%M %p}")
    return "\n".join(lines)

def compute_departure_time(delta: timedelta) -> timedelta:
    # Assuming you want to leave 20 minutes before class starts
    return delta - timedelta(minutes=20)

def compute_lunch_time(delta: timedelta) -> timedelta:
    return delta - timedelta(minutes=45)

def current_sleep_window(now: datetime) -> tuple[datetime, datetime] | None:
    if not SLEEP_ENABLED:
        return None
    today_start = datetime.combine(now.date(), SLEEP_START, tzinfo=TZ)
    start_dt = today_start
    if now < today_start:
        start_dt = today_start - timedelta(days=1)
    end_dt = start_dt + SLEEP_DURATION
    if not (start_dt <= now <= end_dt):
        return None
    return start_dt, end_dt

PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Daybook · University Scheduler</title><style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--bg:#f5f6f8;--paper:#fff;--ink:#22252c;--muted:#8b909b;--line:#eceef1;--blue:#5178ed;--bluebg:#edf1ff;--green:#269b77;--orange:#db9141;--red:#d55d63;--shadow:0 12px 35px #2f3b550a}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif}.shell{max-width:1240px;margin:auto;padding:34px 38px 60px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:34px}.brand{font:800 17px Manrope;letter-spacing:-.5px}.brand span{color:var(--blue)}.date{color:var(--muted);font-size:13px}.nav{display:flex;gap:8px;border-bottom:1px solid var(--line);margin-bottom:30px}.nav button{border:0;background:transparent;padding:13px 18px;color:var(--muted);font:600 14px 'DM Sans';cursor:pointer;border-bottom:2px solid transparent}.nav button.active{color:var(--blue);border-color:var(--blue)}.page{display:none}.page.active{display:block}.heading{display:flex;justify-content:space-between;align-items:end;margin-bottom:23px}.eyebrow{text-transform:uppercase;letter-spacing:1.3px;font:500 10px 'DM Mono';color:var(--blue);margin-bottom:8px}.heading h1{font:700 29px Manrope;letter-spacing:-1px;margin:0}.sub{color:var(--muted);font-size:13px;margin-top:7px}.grid{display:grid;grid-template-columns:1.25fr .75fr;gap:18px}.card{background:var(--paper);border:1px solid var(--line);border-radius:15px;padding:22px;box-shadow:var(--shadow)}.card-title{font:700 14px Manrope;margin:0 0 16px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}.stat{padding:16px;background:#fff;border:1px solid var(--line);border-radius:13px}.stat .label{color:var(--muted);font-size:11px}.stat strong{display:block;margin-top:9px;font:700 22px Manrope}.stat small{font-size:11px;color:var(--muted)}.event{display:grid;grid-template-columns:68px 4px 1fr auto;gap:13px;padding:13px 0;border-top:1px solid var(--line);align-items:center}.event:first-child{border-top:0}.time{font:500 12px 'DM Mono';color:#656b77}.stripe{height:40px;background:var(--blue);border-radius:4px}.event:nth-child(3n) .stripe{background:#54ad91}.event:nth-child(4n) .stripe{background:#e7a950}.event-name{font:600 13px Manrope}.event-detail{font-size:11px;color:var(--muted);margin-top:4px}.duration{font:11px 'DM Mono';color:var(--muted)}.slot-row{display:grid;grid-template-columns:78px 1fr;gap:14px;padding:11px 0;border-top:1px solid var(--line);align-items:start}.slot-row:first-child{border-top:0}.slot-time{font:500 12px 'DM Mono';color:#656b77;padding-top:3px}.slot-items{display:grid;gap:7px}.slot-item{border-left:3px solid var(--blue);padding:2px 10px}.slot-item.personal{border-color:#e7a950}.slot-item.food{border-color:#54ad91}.slot-item .event-detail{line-height:1.5}.slot-continuation{font:10px 'DM Mono';color:var(--muted);margin-left:7px}.slot-empty{font-size:12px;color:var(--muted);padding:2px 10px}.pill{font-size:10px;border-radius:20px;padding:5px 9px;background:var(--bluebg);color:var(--blue);white-space:nowrap}.empty{font-size:13px;color:var(--muted);padding:18px 0}.hero{padding:24px;border-radius:15px;background:#252d3d;color:white;margin-bottom:18px;position:relative;overflow:hidden}.hero:after{content:'';position:absolute;right:-35px;top:-74px;width:220px;height:220px;border-radius:50%;background:#ffffff0c}.hero-label{font:500 10px 'DM Mono';color:#b8c5ff;text-transform:uppercase;letter-spacing:1.4px}.hero h2{font:700 24px Manrope;margin:10px 0 5px}.hero p{font-size:12px;color:#c0c5d0;margin:0}.count{font:500 25px 'DM Mono';letter-spacing:-1px;margin-top:24px}.hero .pill{display:inline-block;background:#ffffff1c;color:white;margin-top:14px}.hero .hero-place{position:absolute;right:22px;bottom:24px;color:#c0c5d0;font-size:12px}.timeline{position:relative}.timeline:before{content:'';position:absolute;left:24px;top:5px;bottom:5px;width:1px;background:var(--line)}.row{display:grid;grid-template-columns:50px 1fr;gap:16px;position:relative;margin:0 0 14px}.row-time{font:11px 'DM Mono';color:var(--muted);padding-top:16px}.row-body{padding:14px 16px;border:1px solid var(--line);border-radius:12px;background:#fff;position:relative}.row-body:before{content:'';position:absolute;left:-33px;top:19px;width:9px;height:9px;border:2px solid var(--blue);background:white;border-radius:50%}.row.current .row-body{border-color:#c9d5ff;background:#f8f9ff}.row.current .row-body:before{background:var(--blue)}.row-title{font:600 13px Manrope}.row-meta{display:flex;justify-content:space-between;margin-top:7px;color:var(--muted);font-size:11px}.important-list{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.important{background:white;border:1px solid var(--line);border-radius:14px;padding:19px;box-shadow:var(--shadow)}.important-top{display:flex;justify-content:space-between;align-items:start}.important h3{font:700 14px Manrope;margin:0}.important .type{font-size:10px;color:var(--blue);background:var(--bluebg);padding:5px 8px;border-radius:12px}.important .days{font:700 26px Manrope;margin-top:22px;letter-spacing:-1px}.important .days span{font:400 12px 'DM Sans';color:var(--muted);letter-spacing:0}.important .when{font:11px 'DM Mono';color:var(--muted);margin-top:7px}.important .course{font-size:11px;color:var(--muted);margin-top:10px}.week-card{margin-top:18px}.week-scroll{overflow-x:auto}.week-grid{display:grid;grid-template-columns:78px repeat(7,minmax(120px,1fr));min-width:1030px}.week-head,.week-cell,.week-time{border-top:1px solid var(--line);border-left:1px solid var(--line);padding:9px 8px}.week-head{font:600 11px Manrope;background:#f8f9fb}.week-head.today{background:#edf1ff;color:var(--blue)}.week-corner{border-left:0}.week-time{font:11px 'DM Mono';color:var(--muted);border-left:0;white-space:nowrap}.week-cell{min-height:58px;font-size:10px}.week-event{border-left:2px solid var(--blue);padding-left:6px;margin:2px 0 6px;line-height:1.4}.week-event.personal{border-color:#e7a950}.week-event.food{border-color:#54ad91}.week-event-title{font:600 10px Manrope}.week-event-detail{color:var(--muted)}.week-empty{color:var(--muted)}.foot{font-size:11px;color:var(--muted);margin-top:15px}.empty-page{grid-column:1/-1}.now{font:500 13px 'DM Mono';color:var(--muted)}@media(max-width:760px){.shell{padding:22px 16px}.grid{grid-template-columns:1fr}.stats{gap:7px}.stat{padding:12px}.stat strong{font-size:18px}.important-list{grid-template-columns:1fr}.week{overflow:auto;grid-template-columns:repeat(7,minmax(90px,1fr))}.heading h1{font-size:24px}.top{margin-bottom:22px}.event{grid-template-columns:58px 4px 1fr auto;gap:9px}}</style></head><body><main class="shell"><header class="top"><div class="brand">daybook<span>.</span></div><div class="date" id="headerDate"></div></header><nav class="nav"><button class="active" data-page="tomorrow">Tomorrow overview</button><button data-page="today">Today dashboard</button><button data-page="important">Important dates</button></nav>
<section class="page active" id="tomorrow"><div class="heading"><div><div class="eyebrow">Plan ahead</div><h1>Tomorrow, at a glance</h1><div class="sub" id="tomorrowDate"></div></div><div class="now" id="liveClock"></div></div><div class="stats" id="tomorrowStats"></div><div class="grid"><div class="card"><h2 class="card-title">Your schedule</h2><div id="tomorrowEvents"></div></div><aside><div class="card" style="margin-bottom:18px"><h2 class="card-title">Coming up</h2><div id="tomorrowTasks"></div></div></aside></div><div class="card week-card"><h2 class="card-title">Full week timetable</h2><div class="week-scroll"><div class="week-grid" id="week"></div></div><div class="foot">All seven days, in 90-minute slots. Events continue into every slot they overlap.</div></div></section>
<section class="page" id="today"><div class="heading"><div><div class="eyebrow">Your day</div><h1>Today dashboard</h1><div class="sub" id="todayDate"></div></div><div class="now" id="todayClock"></div></div><div class="grid"><div class="card"><h2 class="card-title">Full day schedule</h2><div id="todayEvents"></div></div><aside><div id="nowCard"></div><div class="card"><h2 class="card-title">Next event</h2><div id="nextCard"></div></div></aside></div></section>
<section class="page" id="important"><div class="heading"><div><div class="eyebrow">Keep it in view</div><h1>Important dates</h1><div class="sub">Your deadlines and milestones, with a live countdown.</div></div></div><div class="important-list" id="importantList"></div></section></main><script>
const $=id=>document.getElementById(id);document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));b.classList.add('active');$(b.dataset.page).classList.add('active')});
function clock(t){return new Date(t).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}function dateLabel(t,opt={weekday:'long',month:'long',day:'numeric'}){return new Date(t).toLocaleDateString([],{...opt})}function human(ms){let n=Math.max(0,Math.floor(ms/1000)),d=Math.floor(n/86400),h=Math.floor(n%86400/3600),m=Math.floor(n%3600/60),s=n%60;if(d)return `${d}d ${h}h ${m}m`;return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`}function eventHtml(e){return `<div class="event"><div class="time">${clock(e.start)}</div><div class="stripe"></div><div><div class="event-name">${e.title}</div><div class="event-detail">${e.kind} · ${e.place||'Location not set'}</div></div><div class="duration">${e.duration}</div></div>`}function slottedSchedule(events){const interval=90,anchor=8*60+30,baseEnd=20*60+30;let start=anchor,end=baseEnd;for(const e of events){const a=new Date(e.start),b=new Date(e.end),sm=a.getHours()*60+a.getMinutes(),em=b.getHours()*60+b.getMinutes();if(sm<start)start=anchor+Math.floor((sm-anchor)/interval)*interval;if(em>end)end=anchor+Math.ceil((em-anchor)/interval)*interval}let rows=[];for(let t=start;t<end;t+=interval){const slotEnd=t+interval,overlap=events.filter(e=>{const a=new Date(e.start),b=new Date(e.end),sm=a.getHours()*60+a.getMinutes(),em=b.getHours()*60+b.getMinutes();return sm<slotEnd&&em>t});const timeLabel=new Date(2000,0,1,Math.floor(t/60),t%60).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});const contents=overlap.length?overlap.map(e=>{const begins=new Date(e.start).getHours()*60+new Date(e.start).getMinutes()>=t;const sourceClass=e.source==='personal'?' personal':e.source==='food'?' food':'';return `<div class="slot-item${sourceClass}"><div class="event-name">${e.title}${begins?'':'<span class=\"slot-continuation\">Continues</span>'}</div><div class="event-detail">${e.kind} · ${e.place||'Location not set'} · ${e.duration}</div></div>`}).join(''):'<div class="slot-empty">Empty</div>';rows.push(`<div class="slot-row"><div class="slot-time">${timeLabel}</div><div class="slot-items">${contents}</div></div>`)}return rows.join('')}function empty(s){return `<div class="empty">${s}</div>`}
async function refresh(){let d=await(await fetch('/data')).json(),now=new Date(d.now),tom=new Date(d.tomorrow),todayEvents=d.today.events,tomEvents=d.tomorrow.events;$('headerDate').textContent=dateLabel(now,{weekday:'short',month:'short',day:'numeric',year:'numeric'});$('liveClock').textContent=$('todayClock').textContent=now.toLocaleTimeString([],{hour:'numeric',minute:'2-digit',second:'2-digit'});$('tomorrowDate').textContent=dateLabel(tom,{weekday:'long',month:'long',day:'numeric'});$('todayDate').textContent=dateLabel(now);let classCount=tomEvents.filter(x=>x.source==='class').length,free=d.tomorrow.freeHours;$('tomorrowStats').innerHTML=`<div class="stat"><div class="label">COURSE EVENTS</div><strong>${classCount}</strong><small>on your timetable</small></div><div class="stat"><div class="label">PLANNED EVENTS</div><strong>${tomEvents.length}</strong><small>classes, plans and meals</small></div><div class="stat"><div class="label">OPEN TIME</div><strong>${free}h</strong><small>between scheduled events</small></div>`;$('tomorrowEvents').innerHTML=slottedSchedule(tomEvents);$('todayEvents').innerHTML=slottedSchedule(todayEvents);$('tomorrowTasks').innerHTML=d.tomorrow.tasks.length?d.tomorrow.tasks.map(t=>`<div class="event"><div class="time">${t.time}</div><div class="stripe" style="background:#e7a950"></div><div><div class="event-name">${t.title}</div><div class="event-detail">${t.kind}</div></div><span class="pill">Due</span></div>`).join(''):empty('No tasks due tomorrow.');
let cur=d.current;if(cur){$('nowCard').innerHTML=`<div class="hero"><div class="hero-label">Happening now · ${human(cur.remainingMs)} left</div><h2>${cur.title}</h2><p>${cur.kind} · ${clock(cur.start)}–${clock(cur.end)}</p><span class="pill">${cur.place||'Location not set'}</span></div>`}else{$('nowCard').innerHTML=`<div class="hero"><div class="hero-label">Right now</div><h2>You're between events</h2><p>${d.next?`Next up: ${d.next.title} at ${clock(d.next.start)}`:'No more events today'}</p><span class="pill">${d.next?human(new Date(d.next.start)-now)+' until start':'Enjoy the free time'}</span></div>`}let ne=d.next;$('nextCard').innerHTML=ne?`<div class="event"><div class="time">${clock(ne.start)}</div><div class="stripe"></div><div><div class="event-name">${ne.title}</div><div class="event-detail">${ne.kind} · ${ne.place}</div></div><div class="duration">${human(new Date(ne.start)-now)}</div></div>`:empty('No upcoming events today.');
let dates=d.important;$('importantList').innerHTML=dates.length?dates.map(x=>`<article class="important"><div class="important-top"><h3>${x.title}</h3><span class="type">${x.kind}</span></div><div class="days">${x.days}<span> ${x.days===1?'day':'days'} to go</span></div><div class="when">${dateLabel(x.date,{weekday:'long',month:'long',day:'numeric',year:'numeric'})} · ${clock(x.date)}</div><div class="course">${x.course}</div></article>`).join(''):empty('No upcoming important dates. Add dates to DUE_ITEMS in main.py.');
let week=$('week'),interval=90,anchor=510,first=510,last=1230;for(const day of d.week)for(const e of day.events){const a=new Date(e.start),b=new Date(e.end),sm=a.getHours()*60+a.getMinutes(),em=b.getHours()*60+b.getMinutes();if(sm<first)first=anchor+Math.floor((sm-anchor)/interval)*interval;if(em>last)last=anchor+Math.ceil((em-anchor)/interval)*interval}let weekHtml='<div class="week-head week-corner">Time</div>'+d.week.map(day=>`<div class="week-head ${day.today?'today':''}">${day.name} ${day.num}</div>`).join('');for(let t=first;t<last;t+=interval){const label=new Date(2000,0,1,Math.floor(t/60),t%60).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});weekHtml+=`<div class="week-time">${label}</div>`;for(const day of d.week){const items=day.events.filter(e=>{const a=new Date(e.start),b=new Date(e.end),sm=a.getHours()*60+a.getMinutes(),em=b.getHours()*60+b.getMinutes();return sm<t+interval&&em>t});weekHtml+=`<div class="week-cell">${items.length?items.map(e=>{const a=new Date(e.start),sm=a.getHours()*60+a.getMinutes(),source=e.source==='personal'?' personal':e.source==='food'?' food':'';return `<div class="week-event${source}"><div class="week-event-title">${e.title}${sm<t?' · continues':''}</div><div class="week-event-detail">${e.kind}</div></div>`}).join(''):'<span class="week-empty">Empty</span>'}</div>`}}week.innerHTML=weekHtml}
refresh();setInterval(refresh,1000);
</script></body></html>'''

def event_payload(ev: ClassEvent, day) -> dict:
    start = datetime.combine(day, ev.start, tzinfo=TZ)
    return {"title": ev.course, "kind": ev.kind, "place": ev.room, "start": start.isoformat(),
            "end": (start + ev.duration).isoformat(), "duration": f"{int(ev.duration.total_seconds()//60)} min",
            "source": "class" if ev in SCHEDULE else "food" if ev in FOOD_SCHEDULE else "personal"}

def dashboard_data() -> dict:
    now = datetime.now(TZ)
    today = now.date()
    tomorrow = today + timedelta(days=1)
    all_events = SCHEDULE + PERSONAL_SCHEDULE + FOOD_SCHEDULE
    def events_for(day):
        return sorted([event_payload(ev, day) for ev in all_events if ev.weekday == day.weekday()], key=lambda e: e["start"])
    td_events, tm_events = events_for(today), events_for(tomorrow)
    def as_dt(item): return datetime.fromisoformat(item["start"])
    ongoing = next((e for e in td_events if as_dt(e) <= now < datetime.fromisoformat(e["end"])), None)
    future = [e for e in td_events if as_dt(e) > now]
    next_event = future[0] if future else None
    busy = sum(ev.duration.total_seconds() for ev in all_events if ev.weekday == tomorrow.weekday())
    tasks = [{"title": f"{x.title} · {x.kind}", "kind": "Important date", "time": x.due_date.strftime("%I:%M %p")} for x in DUE_ITEMS if x.due_date.date() == tomorrow]
    week = []
    for offset in range(7):
        day = today + timedelta(days=offset)
        week.append({"name": day.strftime("%a").upper(), "num": day.day, "today": offset == 0,
                     "events": events_for(day)})
    dates = [{"title": x.title, "kind": x.kind, "course": x.title, "date": x.due_date.isoformat(),
              "days": (x.due_date.date() - today).days} for x in sorted(DUE_ITEMS, key=lambda x: x.due_date) if x.due_date >= now]
    current = {**ongoing, "remainingMs": (datetime.fromisoformat(ongoing["end"]) - now).total_seconds()*1000} if ongoing else None
    return {"now": now.isoformat(), "today": {"events": td_events}, "tomorrow": {"events": tm_events, "freeHours": max(0, round((24*3600-busy)/3600, 1)), "tasks": tasks},
            "tomorrowDate": tomorrow.isoformat(), "current": current, "next": next_event, "important": dates, "week": week}

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/data":
            body = json.dumps(dashboard_data()).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
        else:
            body = PAGE.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *_args): pass

def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), DashboardHandler)
    print("Daybook dashboard running at http://127.0.0.1:8765 — press Ctrl+C to stop.")
    threading.Timer(0.8, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
