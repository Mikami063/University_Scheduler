# University Scheduler

## Requirements

### Dashboard navigation

Provide four separate pages: Today, Tomorrow, Weekly, and Important. Open to Today by default. Keep the navigation controls visible at the top while the user scrolls.

### Slotted timetable display

The Today and Tomorrow pages show schedules as chronological 90-minute slots instead of event lists. The default timetable runs from 8:30 AM through the 7:00 PM slot. Each row shows its start time and either the scheduled event details or `Empty`, so gaps between events are visible. Extend the timetable when an event falls outside the default hours.

The Weekly page shows the next seven days, starting today, in a full-width grid with the same 90-minute slots. Include every event for each day and show `Empty` in unscheduled cells. Extend the shared time range when an event falls outside the default hours, and show an event in every slot it overlaps.

For example:

| Time | Slot |
| --- | --- |
| 8:30 AM | Lecture — course and event type |
| 10:00 AM | Empty |
| 11:30 AM | Lecture — course and event type |

Mark an event as continuing in slots after its start slot.

Highlight the 90-minute slot matching the current clock time in the Today, Tomorrow, and Weekly timetable views. In the Weekly view, highlight that slot in today's column.

### Sleep and wake-up schedule

Include a daily sleep block starting at 10:00 PM and lasting nine hours, followed by a Wake up routine from 7:00 to 8:00 AM. Show both in the Today, Tomorrow, and Weekly timetables, including the portions that cross midnight.
