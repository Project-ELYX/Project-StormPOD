import spidev, time

def as3935_init(spi, mode="outdoor"):
    """
    Initialize AS3935 lightning/RF sensor for first use.

    Args:
        spi : an spidev.SpiDev() object already opened
        mode: "outdoor" or "indoor" (sets AFE gain)

    Returns:
        dict of key registers after init
    """

    # === helpers ===
    def write_reg(addr, val):
        cmd = 0x00 | (addr & 0x3F)   # write = 0b00aaaaaa
        spi.xfer2([cmd, val & 0x3F])

    def read_reg(addr):
        cmd = 0x40 | (addr & 0x3F)   # read = 0b01aaaaaa
        return spi.xfer2([cmd, 0x00])[1]

    # === 1. Calibrate resonator ===
    spi.xfer2([0x3D, 0x96])  # set bit 7 of reg 0x3D
    time.sleep(0.002)
    spi.xfer2([0x3D, 0x16])  # clear bit 7 again

    # === 2. AFE gain ===
    if mode == "outdoor":
        write_reg(0x00, 0x12)   # outdoor, recommended
    else:
        write_reg(0x00, 0x0E)   # indoor, more sensitive

    # === 3. Noise floor, watchdog, spike rejection ===
    write_reg(0x01, 0x24)   # Noise=2, Watchdog=2
    write_reg(0x02, 0x24)   # Spike rejection=2

    # === 4. Enable interrupts ===
    write_reg(0x08, 0x00)

    # === 5. Return a small reg dump for confirmation ===
    regs = {a: read_reg(a) for a in (0x00,0x01,0x02,0x07,0x08,0x3A,0x3B)}
    return regs

# Example usage:
import spidev

spi = spidev.SpiDev()
spi.open(0,0)           # CE0
spi.max_speed_hz = 500000
spi.mode = 0b01         # SPI mode 1 required

regs = as3935_init(spi, mode="outdoor")
print("AS3935 initialized:", regs)


# decode events
def decode_irq(irq_src: int) -> str:
    """
    Decode AS3935 IRQ source register values into human-readable strings.
    Args:
        irq_src (int): Value from reg 0x03 & 0x0F
    Returns:
        str: Human-readable meaning
    """
    irq_map = {
        0x01: "Noise event",        # background RF noise exceeded threshold
        0x04: "Disturber event",    # man-made RF burst rejected as lightning
        0x08: "Lightning event"     # valid lightning / strong RF transient
    }
    return irq_map.get(irq_src, f"Unknown (0x{irq_src:02X})")
# Example usage:
irq_src = read_reg(0x03) & 0x0F
print("IRQ:", irq_src, decode_irq(irq_src))
