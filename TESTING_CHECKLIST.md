# StormPOD Hardware Testing Checklist

## 🔧 Pre-Testing Setup

### Hardware Connections
- [ ] **Pi CAN Hat** - properly seated on GPIO pins
- [ ] **7" Touchscreen** - HDMI + USB connected
- [ ] **AS3935** - SPI connections (CLK, MOSI, MISO, CS, IRQ on GPIO23)
- [ ] **NEO-M9N GPS** - UART on /dev/serial0 (pins 8,10)
- [ ] **BNO086 IMU** - I2C connections (SDA, SCL)
- [ ] **CAN bus** - 120Ω termination resistors at both ends
- [ ] **ESP32** - flashed with firmware, powered, CAN connected

### Power Requirements
- [ ] **Raspberry Pi** - 5V 3A minimum (recommend 5A for peripherals)
- [ ] **ESP32** - can be powered from Pi or separate 5V supply
- [ ] **Roof pod sensors** - 3.3V from ESP32

## 🧪 Individual Component Testing

### 1. Basic System
```bash
# Check kernel support
lsmod | grep can
ls /sys/class/gpio/

# Check I2C devices
i2cdetect -y 1

# Check SPI
ls /dev/spi*
```

### 2. CAN Interface
```bash
# Setup CAN
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# Test reception
candump can0 &

# Should see messages from ESP32:
# ID 0x010: BME280 data (temp, humidity, pressure)  
# ID 0x011: Wind data (direction, speed raw)
```

### 3. GPS Module
```bash
# Check serial data
sudo cat /dev/serial0 | grep GPRMC
# Should see: $GPRMC,time,A,lat,N,lon,W,speed,course,date...
```

### 4. Lightning Sensor (AS3935)
```bash
# Test SPI communication
python3 -c "
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000
print('SPI OK:', spi.xfer2([0x40, 0x00]))  # Read reg 0x00
spi.close()
"
```

### 5. IMU (BNO086)
```bash
# Test I2C communication
python3 -c "
import board
import busio
i2c = busio.I2C(board.SCL, board.SDA)
print('I2C scan:', [hex(addr) for addr in i2c.scan()])
# Should include 0x4b (BNO086)
"
```

## 🎯 Integration Testing

### Full System Test
```bash
# Run main application with debug output
python3 main.py

# Expected GUI elements:
# - Lightning alerts (test with simulated strikes)
# - Wind speed/direction from ESP32
# - Temperature/humidity/pressure from BME280
# - GPS coordinates and heading
# - IMU orientation data
```

### Data Logging Verification
```bash
# Check if CSV logging works
tail -f bme280_log.csv

# Verify data fields:
# time_utc, temp_C, humidity_%, pressure_hPa, altitude_m
# wind_raw, wind_volts, speed_kph, fix, lat, lon, heading_deg
# lightning, distance_km
```

## 🚨 Common Issues & Solutions

### CAN Bus Problems
- **No messages**: Check 120Ω termination resistors
- **Corrupt data**: Verify bitrate (500kbps), check wiring
- **Interface down**: `sudo ip link set up can0`

### GPS Issues  
- **No fix**: Ensure clear sky view, wait 2-3 minutes for cold start
- **No serial data**: Check `/boot/config.txt` for `enable_uart=1`

### Lightning Sensor
- **No interrupts**: Verify IRQ pin connection (GPIO23)
- **False triggers**: Adjust noise floor in AS3935 config

### IMU Problems
- **I2C errors**: Check pullup resistors (1.8kΩ on SDA/SCL)
- **Address conflicts**: BNO086 default is 0x4B

## ✅ Success Criteria
- [ ] GUI displays all sensor data
- [ ] CAN messages received from ESP32
- [ ] Lightning detection triggers alerts  
- [ ] GPS provides coordinates and heading
- [ ] IMU provides orientation data
- [ ] Data logged to CSV continuously
- [ ] No system crashes over 30-minute test