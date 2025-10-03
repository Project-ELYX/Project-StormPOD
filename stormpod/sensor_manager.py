from sensors.sensor_can import CANReceiver
from sensors.sensor_as3935 import AS3935Sensor
from sensors.sensor_gps import GPSSensor
from sensors.sensor_imu import IMUSensor
from . import logger
import time

class SensorManager:
    def __init__(self):
        self.can = CANReceiver()
        self.gps = GPSSensor()
        self.lightning = AS3935Sensor()
        self.imu = IMUSensor()
        self.latest = {}

    def poll_all(self):
        # Pull CAN-sourced sensor data
        can_data = self.can.read()

        # Pull local sensors (GPS + Lightning + IMU)
        gps_data = self.gps.read()
        lightning_data = self.lightning.read()
        imu_data = self.imu.read()

        # Merge all into one dictionary
        self.latest = {}
        self.latest.update(can_data)
        self.latest.update(gps_data)
        self.latest.update(lightning_data)
        self.latest.update(imu_data)

        # Timestamp (UTC HHMMSS) – GPS if available, else system time
        self.latest["time_utc"] = gps_data.get("time_utc") or time.strftime("%H%M%S", time.gmtime())

        # Log it
        logger.log(self.latest)

    def get_latest(self):
        return self.latest
