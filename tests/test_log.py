from routes.log import TIME_OPTIONS


class TestTimeOptions:
    def test_count(self):
        assert len(TIME_OPTIONS) == 96

    def test_midnight(self):
        assert TIME_OPTIONS[0] == ("00:00", "12:00 AM")

    def test_noon(self):
        assert ("12:00", "12:00 PM") in TIME_OPTIONS

    def test_morning_quarter_hour(self):
        assert ("09:15", "9:15 AM") in TIME_OPTIONS

    def test_last_slot(self):
        assert TIME_OPTIONS[-1] == ("23:45", "11:45 PM")

    def test_values_are_unique_and_sorted(self):
        values = [value for value, _ in TIME_OPTIONS]
        assert values == sorted(values)
        assert len(set(values)) == len(values)
