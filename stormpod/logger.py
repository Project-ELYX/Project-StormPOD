import csv
import os

LOGFILE = "bme280_log.csv"
HEADERS = [
    "time_utc",
    "temp_C", "humidity_%", "pressure_hPa", "altitude_m",
    "wind_raw", "wind_volts", "speed_kph",
    "fix", "lat", "lon", "heading_deg",
    "lightning", "distance_km"
]

def log(data):
    file_exists = os.path.isfile(LOGFILE)
    with open(LOGFILE, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({key: data.get(key, "") for key in HEADERS})
