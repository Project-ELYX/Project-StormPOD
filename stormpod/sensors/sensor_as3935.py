import spidev
import RPi.GPIO as GPIO
import time

class AS3935Sensor:
    def __init__(self, spi_bus=0, spi_device=0, irq_pin=23, mode="outdoor"):
        self.irq_pin = irq_pin
        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.irq_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # use pull-up
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 500000
        self.spi.mode = 0b01
        self.latest_event = None
        self._init_sensor(mode)
        try:
            GPIO.remove_event_detect(self.irq_pin)
            GPIO.add_event_detect(self.irq_pin, GPIO.FALLING,
                                  callback=self._handle_interrupt, bouncetime=2)
        except RuntimeError as e:
            print("GPIO IRQ registration failed:", e)

    def _write_register(self, reg, data):
        cmd = 0x00 | (reg & 0x3F)
        self.spi.xfer2([cmd, data & 0x3F])

    def _read_register(self, reg):
        cmd = 0x40 | (reg & 0x3F)
        return self.spi.xfer2([cmd, 0x00])[1]

    def _init_sensor(self, mode):
        # Resonator calibration
        self.spi.xfer2([0x3D, 0x96])
        time.sleep(0.002)
        self.spi.xfer2([0x3D, 0x16])

        # AFE gain
        if mode == "outdoor":
            self._write_register(0x00, 0x12)
        else:
            self._write_register(0x00, 0x0E)

        # Noise floor, watchdog, spike rejection
        self._write_register(0x01, 0x24)
        self._write_register(0x02, 0x24)

        # Enable interrupts
        self._write_register(0x08, 0x00)

    def _handle_interrupt(self, channel):
        irq_src = self._read_register(0x03) & 0x0F
        if irq_src == 0x08:
            dist = self._read_register(0x07) & 0x3F
            self.latest_event = {"lightning": True, "distance_km": dist, "timestamp": time.time()}
        elif irq_src == 0x01:
            self.latest_event = {"noise": True, "timestamp": time.time()}
        elif irq_src == 0x04:
            self.latest_event = {"disturber": True, "timestamp": time.time()}

    def read(self):
        result = self.latest_event or {}
        self.latest_event = None
        return result
