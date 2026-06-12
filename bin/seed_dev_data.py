from datetime import date, timedelta

import models


def seed():
    """Populate an empty dev DB with packers at realistic points in their stay."""
    today = date.today()

    # Maria: 10 days into a 4-week stay -> week 1 complete, week 2 in progress.
    maria_start = today - timedelta(days=10)
    maria_id = models.create_packer(
        "Maria", maria_start, maria_start + timedelta(days=27),
        maria_start, maria_start + timedelta(days=27),
    )
    # Week 1: 22h logged (3h short of the 25h target).
    for day_offset, start, end, minutes in [
        (0, "09:00", "14:00", 300),
        (1, "09:00", "14:00", 300),
        (2, "09:00", "13:00", 240),
        (3, "09:00", "13:00", 240),
        (4, "09:00", "13:00", 240),
        # Week 2 so far.
        (8, "09:00", "12:00", 180),
        (9, "09:00", "13:00", 240),
    ]:
        models.create_work_entry(
            maria_id, maria_start + timedelta(days=day_offset),
            start, end, minutes, "Garden work",
        )
    # Global excused day in week 1, nudging the week-1 balance toward surplus.
    models.create_excused_day(None, maria_start + timedelta(days=5), "Host day off")

    # Kai: arrives today, week 1, no entries yet.
    models.create_packer(
        "Kai", today, today + timedelta(days=27),
        today, today + timedelta(days=27),
    )
