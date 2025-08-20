#pragma once

// I²C (BME280 + AS5600)
#define I2C_SDA   21
#define I2C_SCL   22

// SPI (MCP3008 anemometer on CH0)
#define SPI_SCK   18
#define SPI_MISO  19
#define SPI_MOSI  23
#define MCP_CS    15
#define ANEMO_CH  0

// CAN (SN65HVD230 transceiver)
#define CAN_TX    5   // ESP32 TXD -> SN65 TXD
#define CAN_RX    4   // ESP32 RXD -> SN65 RXD
// Bus side: SN65 CANH/CANL to the two-wire bus with 120 Ω termination at both ends.
