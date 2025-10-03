"""
AS3935 Lightning / RF Event Sensor Driver
-----------------------------------------
Reusable class for Raspberry Pi projects (StormPOD, Solarwatch, etc).

Features:
- Correct SPI read/write protocol
- Initialization (oscillator calibration, AFE mode, thresholds, interrupts)
- IRQ decoding (Noise / Disturber / Lightning)
- Distance estimation for lightning events
"""

import spidev
import RPi.GPIO as GPIO
import time


class AS3935:
    IRQ_NOISE = 0x01
    IRQ_DISTURBER = 0x04
    IRQ_LIGHTNING = 0x08

    def __init__(self, spi_bus=0, spi_device=0, irq_pin=17, mode="outdoor"):
        """
        Args:
            spi_bus (int): SPI bus (default 0)
            spi_device (int): SPI device (0=CE0, 1=CE1)
            irq_pin (int): BCM pin number for INT pin
            mode (str): "outdoor" or "indoor"
        """
        self.irq_pin = irq_pin
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 500000
        self.spi.mode = 0b01  # AS3935 requires SPI mode 1

        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.irq_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.latest_event = None
        self._init_sensor(mode)

        # Attach interrupt handler
        try:
            GPIO.remove_event_detect(self.irq_pin)
        except Exception:
            pass
        GPIO.add_event_detect(self.irq_pin, GPIO.FALLING,
                              callback=self._irq_callback, bouncetime=2)

    # ------------------------------
    # Low-level SPI helpers
    # ------------------------------
    def _write_register(self, reg, value):
        cmd = 0x00 | (reg & 0x3F)  # write command
        self.spi.xfer2([cmd, value & 0x3F])

    def _read_register(self, reg):
        cmd = 0x40 | (reg & 0x3F)  # read command
        return self.spi.xfer2([cmd, 0x00])[1]

    # ------------------------------
    # Initialization
    # ------------------------------
    def _init_sensor(self, mode):
        # 1. Resonator calibration
        self.spi.xfer2([0x3D, 0x96])
        time.sleep(0.002)
        self.spi.xfer2([0x3D, 0x16])

        # 2. AFE gain (outdoor = less sensitive, indoor = more sensitive)
        if mode.lower() == "outdoor":
            self._write_register(0x00, 0x12)
        else:
            self._write_register(0x00, 0x0E)

        # 3. Noise floor, watchdog, spike rejection
        self._write_register(0x01, 0x24)  # Noise floor + watchdog
        self._write_register(0x02, 0x24)  # Spike rejection

        # 4. Enable interrupts (unmask all)
        self._write_register(0x08, 0x00)

    # ------------------------------
    # IRQ Handling
    # ------------------------------
    def _irq_callback(self, channel):
        irq_src = self._read_register(0x03) & 0x0F
        timestamp = time.time()

        if irq_src == self.IRQ_LIGHTNING:
            dist = self._read_register(0x07) & 0x3F
            self.latest_event = {
                "type": "Lightning",
                "distance_km": dist,
                "timestamp": timestamp
            }
        elif irq_src == self.IRQ_NOISE:
            self.latest_event = {"type": "Noise", "timestamp": timestamp}
        elif irq_src == self.IRQ_DISTURBER:
            self.latest_event = {"type": "Disturber", "timestamp": timestamp}
        else:
            self.latest_event = {"type": "Unknown", "timestamp": timestamp}

    def read_event(self):
        """
        Retrieve the latest event (if any).
        Resets buffer after read.
        """
        evt = self.latest_event
        self.latest_event = None
        return evt

    # ------------------------------
    # Utility
    # ------------------------------
    def close(self):
        GPIO.cleanup(self.irq_pin)
        self.spi.close()
