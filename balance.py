from datetime import date, timedelta


def get_week_number(tracking_start: date, target_date: date) -> int:
    """Return 1-based week number for target_date relative to tracking_start."""
    delta = max(0, (target_date - tracking_start).days)
    return delta // 7 + 1


def get_week_boundaries(tracking_start: date, week_number: int) -> tuple:
    """Return (start_date, end_date) for the given 1-based week number."""
    start = tracking_start + timedelta(days=(week_number - 1) * 7)
    end = start + timedelta(days=6)
    return start, end


def parse_excused_days(raw_excused_days) -> set:
    """Convert SQLite Row objects or string-date dicts to a set of date objects."""
    result = set()
    for r in raw_excused_days:
        d = r["excused_date"]
        if isinstance(d, str):
            d = date.fromisoformat(d)
        result.add(d)
    return result


def _week_target_hours(tracking_start: date, week_number: int, excused_dates: set) -> float:
    """25h target for the week, pro-rated down for each excused day that falls in it."""
    week_start, week_end = get_week_boundaries(tracking_start, week_number)
    excused_count = sum(1 for d in excused_dates if week_start <= d <= week_end)
    return 25 * max(0, 7 - excused_count) / 7


def parse_entries_for_balance(raw_entries) -> list:
    """Convert SQLite Row objects or string-date dicts to plain dicts with date objects."""
    result = []
    for e in raw_entries:
        d = e["entry_date"]
        if isinstance(d, str):
            d = date.fromisoformat(d)
        result.append({
            "entry_date": d,
            "duration_minutes": e["duration_minutes"],
        })
    return result


def compute_balance(entries: list, tracking_start: date, today: date,
                     excused_dates: set = None) -> dict:
    """
    Compute hours balance for a packer.

    entries: list of dicts with 'entry_date' (date) and 'duration_minutes' (int).
             Use parse_entries_for_balance() to convert from SQLite rows.
    excused_dates: set of date objects exempt from the weekly target. Each excused
             day in a week reduces that week's 25h target by 25/7h.
             Use parse_excused_days() to convert from SQLite rows.

    Returns dict with: current_week, completed_weeks, total_hours_worked,
    cumulative_balance, adjusted_target_this_week, this_week_hours,
    this_week_remaining, hours_by_day, week_start, week_end.
    """
    excused_dates = excused_dates or set()
    current_week = get_week_number(tracking_start, today)
    completed_weeks = current_week - 1
    week_start, week_end = get_week_boundaries(tracking_start, current_week)

    total_minutes = 0
    this_week_minutes = 0
    hours_by_day: dict = {}

    for e in entries:
        total_minutes += e["duration_minutes"]
        if week_start <= e["entry_date"] <= week_end:
            this_week_minutes += e["duration_minutes"]
            day_str = str(e["entry_date"])
            hours_by_day[day_str] = hours_by_day.get(day_str, 0) + e["duration_minutes"] / 60

    total_hours = total_minutes / 60
    this_week_hours = this_week_minutes / 60
    completed_week_hours = total_hours - this_week_hours
    completed_weeks_target = sum(
        _week_target_hours(tracking_start, w, excused_dates)
        for w in range(1, completed_weeks + 1)
    )
    cumulative_balance = completed_week_hours - completed_weeks_target
    current_week_target = _week_target_hours(tracking_start, current_week, excused_dates)
    adjusted_target = max(0.0, current_week_target - cumulative_balance)
    this_week_remaining = max(0.0, adjusted_target - this_week_hours)

    return {
        "current_week": current_week,
        "completed_weeks": completed_weeks,
        "total_hours_worked": round(total_hours, 2),
        "cumulative_balance": round(cumulative_balance, 2),
        "adjusted_target_this_week": round(adjusted_target, 2),
        "this_week_hours": round(this_week_hours, 2),
        "this_week_remaining": round(this_week_remaining, 2),
        "hours_by_day": {k: round(v, 2) for k, v in hours_by_day.items()},
        "week_start": str(week_start),
        "week_end": str(week_end),
    }
