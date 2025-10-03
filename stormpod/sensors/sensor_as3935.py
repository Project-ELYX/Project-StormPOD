# Use the improved AS3935 driver - we'll copy it locally
import spidev
import RPi.GPIO as GPIO
import time

class AS3935:
    IRQ_NOISE = 0x01
    IRQ_DISTURBER = 0x04
    IRQ_LIGHTNING = 0x08

    DEFAULT_CONFIG = {
        "mode": "outdoor",
        "noise_floor": 2,
        "watchdog": 2,
        "spike_rejection": 2
    }

    def __init__(self, spi_bus=0, spi_device=0, irq_pin=17, config=None):
        self.irq_pin = irq_pin
        self.config = dict(self.DEFAULT_CONFIG)
        if config:
            self.config.update(config)

        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 500000
        self.spi.mode = 0b01

        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.irq_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.latest_event = None
        self._init_sensor()

        # IRQ setup
        try: 
            GPIO.remove_event_detect(self.irq_pin)
        except: 
            pass
        GPIO.add_event_detect(self.irq_pin, GPIO.FALLING,
                              callback=self._irq_callback, bouncetime=2)

    def _write_register(self, reg, value):
        cmd = 0x00 | (reg & 0x3F)
        self.spi.xfer2([cmd, value & 0x3F])

    def _read_register(self, reg):
        cmd = 0x40 | (reg & 0x3F)
        return self.spi.xfer2([cmd, 0x00])[1]

    def _init_sensor(self):
        # Calibration
        self.spi.xfer2([0x3D, 0x96])
        time.sleep(0.002)
        self.spi.xfer2([0x3D, 0x16])

        # AFE gain
        if self.config["mode"].lower() == "outdoor":
            self._write_register(0x00, 0x12)
        else:
            self._write_register(0x00, 0x0E)

        # Noise floor + watchdog (reg 0x01)
        nf = (self.config["noise_floor"] & 0x07) << 4
        wd = (self.config["watchdog"] & 0x0F)
        self._write_register(0x01, nf | wd)

        # Spike rejection (reg 0x02)
        sr = self.config["spike_rejection"] & 0x0F
        self._write_register(0x02, sr)

        # Enable interrupts
        self._write_register(0x08, 0x00)

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
        evt = self.latest_event
        self.latest_event = None
        return evt

    def close(self):
        GPIO.cleanup(self.irq_pin)
        self.spi.close()

class AS3935Sensor:
    def __init__(self, spi_bus=0, spi_device=0, irq_pin=23, mode="outdoor"):
        # Use the improved driver with configuration
        config = {
            "mode": mode,
            "noise_floor": 2,
            "watchdog": 2,
            "spike_rejection": 2
        }
        self.as3935 = AS3935(spi_bus=spi_bus, spi_device=spi_device, 
                           irq_pin=irq_pin, config=config)

    def read(self):
        """Read the latest lightning event and return in expected format"""
        event = self.as3935.read_event()
        if event is None:
            return {}
        
        # Convert to the format expected by the GUI
        if event.get("type") == "Lightning":
            return {
                "lightning": True, 
                "distance_km": event.get("distance_km", 0),
                "timestamp": event.get("timestamp")
            }
        elif event.get("type") == "Noise":
            return {"noise": True, "timestamp": event.get("timestamp")}
        elif event.get("type") == "Disturber":
            return {"disturber": True, "timestamp": event.get("timestamp")}
        else:
            return {}
    
    def close(self):
        """Clean shutdown"""
        self.as3935.close()
