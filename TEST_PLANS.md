# Test Plans

Running log of manual UI test plans, newest first. Each entry covers a
feature implemented via EPCT; run through it and confirm before marking the
corresponding TODO item done.

## Setup

- **Start the dev server:** `bin/dev.sh` — runs in a detached tmux session
  (`worldpackers-dev`) on `http://127.0.0.1:5051`, using a separate DB
  (`instance/dev.db`) from the live instance (port 5050).
- **Stop:** `bin/dev.sh --stop`
- **Reset state:** `bin/dev.sh --reset` — stops the session, wipes
  `instance/dev.db`, and restarts. An empty DB is auto-seeded (see below).
- **Ops/admin login:** `/ops/login`, password `devpass` (or `$OPS_PASSWORD` if
  set when launching `bin/dev.sh`).
- **Seed data** (`bin/seed_dev_data.py`, auto-applied to an empty DB):
  - **Maria** — 10 days into a 4-week stay. Week 1 complete (22h logged, one
    excused day), week 2 in progress (7h logged so far).
  - **Kai** — arrives today, week 1, no entries yet.

## 2026-06-12 — Single 15-minute time picker

Replaced the hour/minute/AM-PM three-select time picker with a single select
listing all times of day in 15-minute increments (e.g. "12:00 AM", "12:15 AM",
... "11:45 PM").

**Golden path**

1. Go to `/log/<packer_id>` for an active packer.
2. Confirm Start and End each show a single dropdown (not three).
3. Open the Start dropdown — confirm it lists 96 options from "12:00 AM" to
   "11:45 PM" in order, with a blank "--" placeholder first.
4. Pick a Start time (e.g. "9:15 AM") and an End time (e.g. "12:30 PM"), add a
   task description, and save.
5. Confirm the new entry appears in the list below as `09:15–12:30` with the
   correct duration (3.2h) and task description.

**Edit**

6. Click "Edit" on the entry just created.
7. Confirm the Start dropdown pre-selects "9:15 AM" and the End dropdown
   pre-selects "12:30 PM".
8. Change the End time to something earlier than Start (e.g. End = "9:00 AM")
   and save.
9. Confirm an error "End time must be after start time." is shown, and both
   dropdowns retain the values you selected (not reset to "--").
10. Fix the End time and save successfully; confirm the entry list updates.

**Edge cases**

- Leaving a dropdown on "--" and submitting should be blocked by the browser
  (`required` attribute) — form should not submit.
- Delete the test entry afterward to keep dev data clean.
