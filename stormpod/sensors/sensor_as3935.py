import spidev
import RPi.GPIO as GPIO
import time

class AS3935Sensor:
    def __init__(self, spi_bus=0, spi_device=0, irq_pin=23):
        self.irq_pin = irq_pin
        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.irq_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 500000
        self.spi.mode = 0b01
        self.latest_strike = None
        self._init_sensor()
        try:
            GPIO.remove_event_detect(self.irq_pin)
            GPIO.add_event_detect(self.irq_pin, GPIO.FALLING, callback=self._handle_interrupt, bouncetime=300)
        except RuntimeError as e:
            print("GPIO IRQ registration failed:", e)

    def _write_register(self, reg, data):
        reg = (reg & 0x3F) | 0x40
        self.spi.xfer2([reg, data])

    def _read_register(self, reg):
        reg = reg & 0x3F
        result = self.spi.xfer2([reg, 0x00])
        return result[1]
    
    def _init_sensor(self):
        self._write_register(0x00, 0x24)
        self._write_register(0x08, 0x00)
        self._write_register(0x03, 0x96)

    def _handle_interrupt(self, channel):
        int_src = self._read_register(0x03) & 0x0F
        if int_src == 0x08:
            dist_km = self._read_register(0x07)
            self.latest_strike = {"lightning": True, "distance_km": dist_km, "timestamp": time.time()}
        elif int_src == 0x01:
            self.latest_strike = {"lightning": False, "noise": True}
        elif int_src == 0x04:
            self.latest_strike = {"lightning": False, "disturber": True}

    def read(self):
        result = self.latest_strike or {"lightning": False}
        self.latest_strike = None
        return result
