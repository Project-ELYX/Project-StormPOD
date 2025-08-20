# irq_listener.py (run with sudo)

import RPi.GPIO as GPIO
import time
import spidev
import json
import os

IRQ_PIN = 17
OUTPUT_FILE = "/tmp/lightning_status.json"

class AS3935:
    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 500000
        self.spi.mode = 0b01

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        try:
            GPIO.remove_event_detect(IRQ_PIN)
        except RuntimeError:
            pass

        GPIO.add_event_detect(IRQ_PIN, GPIO.FALLING,
                              callback=self.handle_interrupt,
                              bouncetime=300)
        self._init_sensor()

    def _init_sensor(self):
        self._write_register(0x00, 0x24)
        self._write_register(0x08, 0x00)
        self._write_register(0x03, 0x96)

    def _write_register(self, reg, data):
        self.spi.xfer2([(reg & 0x3F) | 0x40, data])

    def _read_register(self, reg):
        return self.spi.xfer2([reg & 0x3F, 0x00])[1]

    def handle_interrupt(self, channel):
        int_src = self._read_register(0x03) & 0x0F
        data = {"timestamp": time.time()}

        if int_src == 0x08:
            data.update({"lightning": True,
                         "distance_km": self._read_register(0x07)})
        elif int_src == 0x01:
            data.update({"noise": True})
        elif int_src == 0x04:
            data.update({"disturber": True})

        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f)
        os.chmod(OUTPUT_FILE, 0o666)

if __name__ == "__main__":
    sensor = AS3935()
    print("Lightning IRQ listener running. Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
