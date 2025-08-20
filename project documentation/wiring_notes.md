BME280 → I²C on ESP32 pins SDA=21, SCL=22.

AS5600 → I²C (same bus).

MCP3008 (anemometer on CH0) → SPI SCK=18, MISO=19, MOSI=23, CS=15.

SN65HVD230 → CAN_TX=GPIO5 to TXD, CAN_RX=GPIO4 to RXD, 3.3 V, GND; bus to CANH/CANL with 120 Ω at each end

Bitrate = 500 kbps (Pi brings up can0@500k and decodes exactly these frames)