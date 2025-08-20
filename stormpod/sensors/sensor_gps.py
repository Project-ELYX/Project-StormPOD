import serial
import time

class GPSSensor:
    def __init__(self, port="/dev/serial0", baud=38400):
        self.ser = serial.Serial(port, baud, timeout=1)
        self.latest = {
            "lat": None,
            "lon": None,
            "fix": False,
            "speed_kph": 0.0,
            "time_utc": None
        }
    
    def _parse_latlon(self, raw, direction):
        if not raw or raw == "0":
            return None
        deg = int(raw[:2])
        minutes = float(raw[2:])
        coord = deg + minutes / 60.0
        return coord if direction in ["N", "E"] else -coord
    
    def _parse_line(self, line):
        if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
            parts = line.split(",")
            if parts[2] == "A":
                self.latest["fix"] = True
                self.latest["lat"] = self._parse_latlon(parts[3], parts[4])
                self.latest["lon"] = self._parse_latlon(parts[5], parts[6])
                self.latest["speed_kph"] = round(float(parts[7]) * 1.852, 2)
                self.latest["time_utc"] = parts[1][:6]
            try:
                heading = float(parts[8])
                self.latest["heading_deg"] = heading
            except:
                self.latest["heading_deg"] = None
            else:
                self.latest["fix"] = False

    def read(self):
        for _ in range(10):
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            self._parse_line(line)
        return self.latest
