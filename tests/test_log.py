from routes.log import _to_24h, _from_24h


class TestTo24h:
    def test_midnight(self):
        assert _to_24h("12", "00", "AM") == "00:00"

    def test_noon(self):
        assert _to_24h("12", "00", "PM") == "12:00"

    def test_morning_hour(self):
        assert _to_24h("9", "15", "AM") == "09:15"

    def test_evening_hour(self):
        assert _to_24h("9", "45", "PM") == "21:45"

    def test_eleven_pm(self):
        assert _to_24h("11", "30", "PM") == "23:30"


class TestFrom24h:
    def test_midnight(self):
        assert _from_24h("00:00") == ("12", "00", "AM")

    def test_noon(self):
        assert _from_24h("12:00") == ("12", "00", "PM")

    def test_morning_hour(self):
        assert _from_24h("09:15") == ("9", "15", "AM")

    def test_evening_hour(self):
        assert _from_24h("21:45") == ("9", "45", "PM")

    def test_eleven_pm(self):
        assert _from_24h("23:30") == ("11", "30", "PM")


class TestRoundTrip:
    def test_all_hours_and_minutes(self):
        for h in range(24):
            for m in ("00", "15", "30", "45"):
                time_str = f"{h:02d}:{m}"
                hour12, minute, ampm = _from_24h(time_str)
                assert _to_24h(hour12, minute, ampm) == time_str
