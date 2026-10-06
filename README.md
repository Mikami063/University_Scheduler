# University Scheduler

## Requirements

### Slotted timetable display

The Today dashboard and Tomorrow overview show schedules as chronological 90-minute slots instead of event lists. The default timetable runs from 8:30 AM through the 7:00 PM slot. Each row shows its start time and either the scheduled event details or `Empty`, so gaps between events are visible. Extend the timetable when an event falls outside the default hours.

The weekly timetable shows the next seven days, starting today, in a full-width grid with the same 90-minute slots. Include every event for each day and show `Empty` in unscheduled cells. Extend the shared time range when an event falls outside the default hours, and show an event in every slot it overlaps.

For example:

| Time | Slot |
| --- | --- |
| 8:30 AM | Lecture — course and event type |
| 10:00 AM | Empty |
| 11:30 AM | Lecture — course and event type |

Mark an event as continuing in slots after its start slot.
