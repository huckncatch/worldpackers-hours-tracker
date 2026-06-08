# WorldPackers Hours Tracker — TODO

## Pending

- [ ] **Admin password gate** — Add a simple password prompt to gate entry to `/ops`. No full auth system needed; a single shared password for host use is sufficient.

- [ ] **Packer dates on dashboard card** — Show tracking/stay date range on each packer's dashboard card. Currently a future packer (not yet arrived) and an active packer look identical. Consider showing arrival date, departure date, and/or current week number relative to tracking start.

- [ ] **All entries list view** — Add a dedicated view showing all logged work entries for a packer (chronological list). Separate from the log-entry form's inline list, which only shows recent entries. Useful for reviewing a packer's full history.

## Completed

- [x] Project scaffold, DB schema, routes, balance logic, full UI (2026-06-07)
- [x] LaunchAgent + tmux auto-start (2026-06-07)
- [x] Obscure admin URL (`/ops`), delete packer, align action buttons (2026-06-08)
- [x] 15-minute time selects, fix form field overflow (2026-06-08)
