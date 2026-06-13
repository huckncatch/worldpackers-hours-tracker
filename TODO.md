# WorldPackers Hours Tracker — TODO

## Pending

- [ ] **Packer dates on dashboard card** — Show tracking/stay date range on each packer's dashboard card. Currently a future packer (not yet arrived) and an active packer look identical. Consider showing arrival date, departure date, and/or current week number relative to tracking start.

- [ ] **All entries list view** — Add a dedicated view showing all logged work entries for a packer (chronological list). Separate from the log-entry form's inline list, which only shows recent entries. Useful for reviewing a packer's full history.

- [ ] **Swipe-to-delete on entries list** — Remove the inline ✕ delete button from the log entry page. Replace with either (a) swipe-left gesture to reveal a delete action (CSS/JS), or (b) move delete into the edit form so Edit is the only visible action in the list. Option (b) is simpler and keeps the list cleaner.

## Completed

- [x] Project scaffold, DB schema, routes, balance logic, full UI (2026-06-07)
- [x] LaunchAgent + tmux auto-start (2026-06-07)
- [x] Obscure admin URL (`/ops`), delete packer, align action buttons (2026-06-08)
- [x] 15-minute time selects, fix form field overflow (2026-06-08)
- [x] Admin password gate (2026-06-09)
- [x] Multi-column time picker (hour/minute/AM-PM selects) (2026-06-09)
- [x] Self-contained deploy setup — `bin/install.sh` provisions `.env`, venv/deps, LaunchAgent, and starts the server (2026-06-09)
- [x] Cross-architecture tmux support — `bin/start.sh` detects Homebrew's tmux path on both Apple Silicon and Intel Macs (2026-06-11)
- [x] Excused days (blocked-out dates) — new `excused_days` table (global or per-packer), admin UI to add/remove, balance logic pro-rates each week's 25h target by `25 × (7 − N) / 7` (2026-06-11)
- [x] Single 15-minute time picker — replaced hour/minute/AM-PM three-select with one select of "HH:MM" 24h values labeled in 12h format (2026-06-12)
