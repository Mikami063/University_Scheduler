# University Scheduler

## Requirements

### Slotted timetable display

The Today dashboard and Tomorrow overview show schedules as chronological 90-minute slots instead of event lists. The default timetable runs from 8:30 AM through the 7:00 PM slot. Each row shows its start time and either the scheduled event details or `Empty`, so gaps between events are visible. Extend the timetable when an event falls outside the default hours.

For example:

| Time | Slot |
| --- | --- |
| 8:30 AM | Lecture — course and event type |
| 10:00 AM | Empty |
| 11:30 AM | Lecture — course and event type |

Show an event in every slot it overlaps. Mark it as continuing in slots after its start slot.
