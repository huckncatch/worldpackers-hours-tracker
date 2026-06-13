import pytest
from datetime import date
from balance import compute_balance, get_week_number, parse_entries_for_balance, parse_excused_days


def entry(d: date, minutes: int):
    return {"entry_date": d, "duration_minutes": minutes}


class TestWeekNumber:
    def test_day_1_is_week_1(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 1)) == 1

    def test_day_7_is_still_week_1(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 7)) == 1

    def test_day_8_is_week_2(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 8)) == 2

    def test_day_14_is_week_2(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 14)) == 2

    def test_day_15_is_week_3(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 15)) == 3


class TestBalance:
    def test_zero_hours_zero_balance(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Day 8 = week 2
        result = compute_balance([], start, today)
        assert result["completed_weeks"] == 1
        assert result["cumulative_balance"] == -25.0  # owed 25, worked 0
        assert result["adjusted_target_this_week"] == 50.0  # 25 + 25 catch-up

    def test_exactly_on_target_after_one_week(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Start of week 2
        entries = [entry(date(2026, 6, d), 300) for d in range(1, 6)]  # 5×5h = 25h
        result = compute_balance(entries, start, today)
        assert result["cumulative_balance"] == 0.0
        assert result["adjusted_target_this_week"] == 25.0

    def test_surplus_reduces_next_week_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        # Worked 30h in week 1 (5h surplus)
        entries = [entry(date(2026, 6, d), 360) for d in range(1, 6)]  # 5×6h = 30h
        result = compute_balance(entries, start, today)
        assert result["cumulative_balance"] == 5.0
        assert result["adjusted_target_this_week"] == 20.0

    def test_deficit_increases_next_week_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        # Worked 20h in week 1 (5h deficit)
        entries = [entry(date(2026, 6, d), 240) for d in range(1, 6)]  # 5×4h = 20h
        result = compute_balance(entries, start, today)
        assert result["cumulative_balance"] == -5.0
        assert result["adjusted_target_this_week"] == 30.0

    def test_this_week_hours_counted_separately(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 10)  # Week 2, mid-week
        # Week 1: exactly 25h. Week 2 so far: 6h
        week1 = [entry(date(2026, 6, d), 300) for d in range(1, 6)]
        week2 = [entry(date(2026, 6, 9), 360)]  # 6h on day 9
        result = compute_balance(week1 + week2, start, today)
        assert result["cumulative_balance"] == 0.0      # week 1 was exactly 25
        assert result["this_week_hours"] == 6.0
        assert result["adjusted_target_this_week"] == 25.0
        assert result["this_week_remaining"] == 19.0

    def test_adjusted_target_never_goes_negative(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)
        # Worked 60h in week 1 (35h surplus — extreme case)
        entries = [entry(date(2026, 6, d), 720) for d in range(1, 6)]  # 5×12h
        result = compute_balance(entries, start, today)
        assert result["adjusted_target_this_week"] == 0.0

    def test_first_week_no_completed_weeks(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 5)  # Still in week 1
        entries = [entry(date(2026, 6, 3), 180)]  # 3h so far
        result = compute_balance(entries, start, today)
        assert result["completed_weeks"] == 0
        assert result["cumulative_balance"] == 0.0   # No completed weeks to evaluate
        assert result["this_week_hours"] == 3.0
        assert result["adjusted_target_this_week"] == 25.0


class TestExcusedDays:
    def test_excused_day_in_completed_week_reduces_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        excused = {date(2026, 6, 3)}  # one excused day in week 1
        result = compute_balance([], start, today, excused)
        # Week 1 target drops from 25 to 25*6/7 = 21.43
        assert result["cumulative_balance"] == -21.43
        assert result["adjusted_target_this_week"] == 46.43

    def test_excused_day_in_current_week_reduces_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 3)  # Still in week 1, no completed weeks
        excused = {date(2026, 6, 5)}  # excused day later this week
        result = compute_balance([], start, today, excused)
        assert result["completed_weeks"] == 0
        assert result["cumulative_balance"] == 0.0
        # Week 1 target drops from 25 to 25*6/7 = 21.43
        assert result["adjusted_target_this_week"] == 21.43

    def test_multiple_excused_days_same_week(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        excused = {date(2026, 6, 3), date(2026, 6, 4)}  # two excused days in week 1
        result = compute_balance([], start, today, excused)
        # Week 1 target drops from 25 to 25*5/7 = 17.86
        assert result["cumulative_balance"] == -17.86
        assert result["adjusted_target_this_week"] == 42.86

    def test_all_seven_days_excused_zeroes_week_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        excused = {date(2026, 6, d) for d in range(1, 8)}  # all of week 1
        result = compute_balance([], start, today, excused)
        # Week 1 target is 0, so no debt accrues and week 2 stays at the normal 25
        assert result["cumulative_balance"] == 0.0
        assert result["adjusted_target_this_week"] == 25.0

    def test_excused_date_outside_tracking_range_has_no_effect(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        entries = [entry(date(2026, 6, d), 300) for d in range(1, 6)]  # exactly 25h
        excused = {date(2026, 5, 25)}  # before tracking start
        result = compute_balance(entries, start, today, excused)
        assert result["cumulative_balance"] == 0.0
        assert result["adjusted_target_this_week"] == 25.0


class TestParseExcusedDays:
    def test_string_dates_converted(self):
        raw = [{"excused_date": "2026-06-03"}, {"excused_date": "2026-06-04"}]
        parsed = parse_excused_days(raw)
        assert parsed == {date(2026, 6, 3), date(2026, 6, 4)}

    def test_duplicate_dates_deduplicated(self):
        raw = [{"excused_date": "2026-06-03"}, {"excused_date": "2026-06-03"}]
        parsed = parse_excused_days(raw)
        assert parsed == {date(2026, 6, 3)}


class TestParseEntries:
    def test_sqlite_row_dicts_converted(self):
        entries = [
            {"entry_date": "2026-06-03", "duration_minutes": 180},
        ]
        parsed = parse_entries_for_balance(entries)
        assert parsed[0]["entry_date"] == date(2026, 6, 3)
        assert parsed[0]["duration_minutes"] == 180

    def test_date_objects_passed_through(self):
        d = date(2026, 6, 3)
        entries = [{"entry_date": d, "duration_minutes": 90}]
        parsed = parse_entries_for_balance(entries)
        assert parsed[0]["entry_date"] == d
        assert parsed[0]["duration_minutes"] == 90
