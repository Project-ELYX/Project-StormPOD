import time
import board
import busio
import adafruit_bno08x
from adafruit_bno08x.i2c import BNO08X_I2C

class IMUSensor:
    def __init__(self, address=0x4B):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.bno = BNO08X_I2C(i2c, address=address)
        time.sleep(1.5)
        self.last_heading = None
        self.bno_ready = False

        for attempt in range(3):
            try:
                self.bno.enable_feature(adafruit_bno08x.BNO_REPORT_ROTATION_VECTOR)
                print(f"✅ IMU rotation vector enabled on try {attempt+1}")
                self.bno_ready = True
                break
            except Exception as e:
                print(f"⚠️ IMU enable failed on try {attempt+1}: {e}")
                time.sleep(0.5)

        if not self.bno_ready:
            print("❌ IMU failed to initialize. Heading data will be unavailable.")

    def read(self):
        if not self.bno_ready:
            return {"heading_deg": None}
        try:
            data = self.bno.rotation_vector
            if data is None:
                return {"heading_deg": self.last_heading}
            w, x, y, z = data
            yaw = self._quat_to_yaw(w, x, y, z)
            self.last_heading = round(yaw, 1)
            return {"heading_deg": self.last_heading}
        except Exception as e:
            print(f"⚠️ IMU read error: {e}")
            return {"heading_deg": self.last_heading}

    def _quat_to_yaw(self, w, x, y, z):
        import math
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        yaw_deg = (math.degrees(yaw) + 360) % 360
        return yaw_deg
