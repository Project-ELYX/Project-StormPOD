import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from stormpod.sensors.sensor_gps import GPSSensor


def _gps_sensor():
    gps = GPSSensor.__new__(GPSSensor)
    gps.latest = {
        "lat": None,
        "lon": None,
        "fix": False,
        "speed_kph": 0.0,
        "time_utc": None,
    }
    return gps


def test_parse_line_with_fix():
    gps = _gps_sensor()
    line = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
    gps._parse_line(line)
    assert gps.latest["fix"] is True
    assert gps.latest["lat"] == pytest.approx(48.1173, abs=1e-4)
    assert gps.latest["lon"] == pytest.approx(11.516666, abs=1e-4)
    assert gps.latest["speed_kph"] == pytest.approx(41.48)
    assert gps.latest["time_utc"] == "123519"
    assert gps.latest["heading_deg"] == pytest.approx(84.4)


def test_parse_line_without_fix():
    gps = _gps_sensor()
    line = "$GPRMC,123519,V,,,,,,,230394,,,N*53"
    gps._parse_line(line)
    assert gps.latest["fix"] is False
    assert gps.latest["lat"] is None
    assert gps.latest["lon"] is None
    assert "heading_deg" not in gps.latest
