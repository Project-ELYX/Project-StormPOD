import can

class CANReceiver:
    def __init__(self, channel='can0', bitrate=500000):
        self.bus = can.interface.Bus(channel=channel, bustype='socketcan')
        self.latest = {
            "temp_C": None,
            "humidity_%": None,
            "pressure_hPa": None,
            "angle_deg": None,
            "wind_raw": None,
            "wind_volts": None,
            "speed_kph": None
        }

    def update(self):
        msg = self.bus.recv(timeout=0.1)
        if msg is None:
            return

        if msg.arbitration_id == 0x10 and msg.dlc == 6:
            t = (msg.data[0] << 8) | msg.data[1]
            h = (msg.data[2] << 8) | msg.data[3]
            p = (msg.data[4] << 8) | msg.data[5]
            self.latest.update({
                "temp_C": t / 10.0,
                "humidity_%": h / 10.0,
                "pressure_hPa": p / 10.0
            })

        elif msg.arbitration_id == 0x11 and msg.dlc == 4:
            angle_raw = (msg.data[0] << 8) | msg.data[1]
            wind_raw = (msg.data[2] << 8) | msg.data[3]
            volts = (wind_raw / 1023.0) * 3.3
            volts = min(volts, 2.2)

            ZERO_WIND_VOLTAGE = 0.4
            MAX_SENSOR_VOLTAGE = 2.0
            MAX_WIND_KPH = 116.6

            if volts <= ZERO_WIND_VOLTAGE:
                wind_kph = 0.0
            else:
                adjusted = volts - ZERO_WIND_VOLTAGE
                scale = MAX_WIND_KPH / (MAX_SENSOR_VOLTAGE - ZERO_WIND_VOLTAGE)
                wind_kph = round(adjusted * scale, 1)

            self.latest.update({
                "angle_deg": angle_raw / 10.0,
                "wind_raw": wind_raw,
                "wind_volts": round(volts, 3),
                "speed_kph": wind_kph
            })

    def read(self):
        self.update()
        return self.latest
