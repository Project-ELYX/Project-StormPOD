# Project-StormPOD

Coding and functions for the experimental StormPOD hardware. Except not the tested version, because Windows comitted genocide on my Debian partition.

---

## ✅ Current Hardware Breakdown

### 🚚 Cab-Mounted (Pi Side)

| Component                              | Purpose/Description                                 |
|-----------------------------------------|-----------------------------------------------------|
| **Raspberry Pi 4B**                     | Main logic and GUI system                           |
| Waveshare 7" HDMI Capacitive Touchscreen| Display UI                                          |
| Sparkfun AS3935 Lightning Sensor        | Interrupt-based lightning detection                 |
| Sparkfun NEO-M9N GPS                    | GPS + heading for wind correction and display       |
| SparkFun BNO086 IMU                     | Yaw/tilt/rotation vector for wind vector correction |
| RTL-SDR Blog v4                         | Optional NOAA/ECCC weather alert monitoring         |
| CAN Hat                                 | CAN interface, installed on Raspberry Pi            |

---

### 🛰️ Roof Pod

| Component                        | Purpose/Description                                  |
|-----------------------------------|------------------------------------------------------|
| ESP32 Dev Board (ELEGOO)          | Sensor hub for CAN broadcast to in-cab system        |
| Waveshare SN65HVD230              | CAN PHY + bus integration                            |
| BME280                            | Temperature/humidity/pressure                        |
| Adafruit MCP3008 ADC              | Reads analog wind speed sensor                       |
| AS5600 Magnetic Encoder           | Wind vane directional data *(in development)*        |
| Adafruit Anemometer (1733)        | Analog wind voltage output, scaled
