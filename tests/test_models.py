import pytest
from datetime import date
import models


def test_create_and_get_packer(app):
    with app.app_context():
        packer_id = models.create_packer(
            name="Maria",
            arrival_date=date(2026, 6, 1),
            departure_date=date(2026, 6, 28),
            tracking_start_date=date(2026, 6, 2),
            tracking_end_date=date(2026, 6, 27),
        )
        packer = models.get_packer(packer_id)
        assert packer["name"] == "Maria"
        assert packer["locked"] == 0
        assert packer["hidden"] == 0


def test_list_active_packers(app):
    with app.app_context():
        models.create_packer("Active", date(2026,6,1), date(2026,6,28),
                              date(2026,6,1), date(2026,6,28))
        hidden_id = models.create_packer("Hidden", date(2026,6,1), date(2026,6,28),
                                          date(2026,6,1), date(2026,6,28))
        models.set_packer_hidden(hidden_id, True)

        active = models.list_active_packers()
        names = [p["name"] for p in active]
        assert "Active" in names
        assert "Hidden" not in names


def test_create_work_entry(app):
    with app.app_context():
        packer_id = models.create_packer("Kai", date(2026,6,1), date(2026,6,28),
                                          date(2026,6,1), date(2026,6,28))
        entry_id = models.create_work_entry(
            packer_id=packer_id,
            entry_date=date(2026, 6, 5),
            start_time="09:00",
            end_time="12:00",
            duration_minutes=180,
            task_description="Garden work",
        )
        entries = models.get_entries_for_packer(packer_id)
        assert len(entries) == 1
        assert entries[0]["duration_minutes"] == 180
        assert entries[0]["task_description"] == "Garden work"


def test_delete_work_entry(app):
    with app.app_context():
        packer_id = models.create_packer("Dee", date(2026,6,1), date(2026,6,28),
                                          date(2026,6,1), date(2026,6,28))
        entry_id = models.create_work_entry(packer_id, date(2026,6,5),
                                             "10:00", "11:00", 60, None)
        models.delete_work_entry(entry_id)
        entries = models.get_entries_for_packer(packer_id)
        assert len(entries) == 0


def test_audit_log_records_operation(app):
    with app.app_context():
        models.log_audit(
            operation="CREATE",
            entity="entry",
            entity_id=1,
            packer_name="Maria",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.42",
        )
        log = models.get_recent_audit(limit=5)
        assert len(log) == 1
        assert log[0]["operation"] == "CREATE"
        assert log[0]["packer_name"] == "Maria"


def test_excused_day_global_applies_to_all_packers(app):
    with app.app_context():
        packer_a = models.create_packer("A", date(2026,6,1), date(2026,6,28),
                                         date(2026,6,1), date(2026,6,28))
        packer_b = models.create_packer("B", date(2026,6,1), date(2026,6,28),
                                         date(2026,6,1), date(2026,6,28))
        models.create_excused_day(packer_id=None, excused_date=date(2026, 6, 10),
                                   reason="Host day off")

        for pid in (packer_a, packer_b):
            days = models.get_excused_days_for_packer(pid)
            assert len(days) == 1
            assert days[0]["excused_date"] == "2026-06-10"
            assert days[0]["packer_id"] is None


def test_excused_day_per_packer_scoped(app):
    with app.app_context():
        packer_a = models.create_packer("A", date(2026,6,1), date(2026,6,28),
                                         date(2026,6,1), date(2026,6,28))
        packer_b = models.create_packer("B", date(2026,6,1), date(2026,6,28),
                                         date(2026,6,1), date(2026,6,28))
        models.create_excused_day(packer_id=packer_a, excused_date=date(2026, 6, 12),
                                   reason="Personal travel")

        assert len(models.get_excused_days_for_packer(packer_a)) == 1
        assert len(models.get_excused_days_for_packer(packer_b)) == 0


def test_list_all_excused_days_resolves_packer_name(app):
    with app.app_context():
        packer_a = models.create_packer("A", date(2026,6,1), date(2026,6,28),
                                         date(2026,6,1), date(2026,6,28))
        models.create_excused_day(packer_id=packer_a, excused_date=date(2026, 6, 12),
                                   reason="Personal travel")
        models.create_excused_day(packer_id=None, excused_date=date(2026, 6, 10),
                                   reason="Host day off")

        days = models.list_all_excused_days()
        by_date = {d["excused_date"]: d for d in days}
        assert by_date["2026-06-12"]["packer_name"] == "A"
        assert by_date["2026-06-10"]["packer_name"] is None


def test_delete_excused_day(app):
    with app.app_context():
        excused_id = models.create_excused_day(packer_id=None, excused_date=date(2026, 6, 10),
                                                 reason="Host day off")
        models.delete_excused_day(excused_id)
        assert models.list_all_excused_days() == []


def test_delete_packer_cascades_per_packer_excused_days_only(app):
    with app.app_context():
        packer_a = models.create_packer("A", date(2026,6,1), date(2026,6,28),
                                         date(2026,6,1), date(2026,6,28))
        models.create_excused_day(packer_id=packer_a, excused_date=date(2026, 6, 12),
                                   reason="Personal travel")
        models.create_excused_day(packer_id=None, excused_date=date(2026, 6, 10),
                                   reason="Host day off")

        models.delete_packer(packer_a)

        remaining = models.list_all_excused_days()
        assert len(remaining) == 1
        assert remaining[0]["excused_date"] == "2026-06-10"
