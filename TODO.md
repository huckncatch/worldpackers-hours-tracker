# WorldPackers Hours Tracker — TODO

## Pending

- [ ] **Packer dates on dashboard card** — Show tracking/stay date range on each packer's dashboard card. Currently a future packer (not yet arrived) and an active packer look identical. Consider showing arrival date, departure date, and/or current week number relative to tracking start.

- [ ] **All entries list view** — Add a dedicated view showing all logged work entries for a packer (chronological list). Separate from the log-entry form's inline list, which only shows recent entries. Useful for reviewing a packer's full history.

- [ ] **Swipe-to-delete on entries list** — Remove the inline ✕ delete button from the log entry page. Replace with either (a) swipe-left gesture to reveal a delete action (CSS/JS), or (b) move delete into the edit form so Edit is the only visible action in the list. Option (b) is simpler and keeps the list cleaner.

- [ ] **Excused days (blocked-out dates)** — Allow the host to mark specific dates as exempt from hours calculations (e.g. camping trips, travel days, host days off). Excused days should pro-rate the weekly target: a week with N excused days has a target of `25 × (7 − N) / 7` hours instead of the full 25. Needs: a new `excused_days` table (packer_id or NULL for all packers, date, reason); admin UI to add/remove excused days; balance logic updated to subtract excused days from each week's target. Consider whether excused days apply globally (all packers) or per-packer.

- [ ] **Self-contained deploy setup** — Move `start-worldpackers.sh` from `~/config/bin/` into this repo (e.g. `bin/start.sh`). Add a `bin/install.sh` script that: creates the venv + installs deps, copies/symlinks the LaunchAgent plist to `~/Library/LaunchAgents/`, loads it with `launchctl`, and runs the start script. After a fresh `git clone` on a new machine, `bin/install.sh` should be all that's needed to have the server auto-starting. Update the plist to reference the in-repo script path.

## Completed

- [x] Project scaffold, DB schema, routes, balance logic, full UI (2026-06-07)
- [x] LaunchAgent + tmux auto-start (2026-06-07)
- [x] Obscure admin URL (`/ops`), delete packer, align action buttons (2026-06-08)
- [x] 15-minute time selects, fix form field overflow (2026-06-08)
- [x] Admin password gate (2026-06-09)
- [x] Multi-column time picker (hour/minute/AM-PM selects) (2026-06-09)
