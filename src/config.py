from array import array

CSV_SPLIT = "\t"  # used to split printed values
T_LCD_REFRESH_SETUP = 1  # fast for manual correction
T_LCD_REFRESH_MEAS = 5  # slower for measuring
T_SD_WRITE = 30  # how often to write to SD

# potentiometer and SW2 pins
PIN_POT = 32
PIN_SW2 = 4

# i2c bus pins - ADC, LCD
I2C_SDA = 21
I2C_SCK = 22
I2C_FREQ = 400000

LCD_ADDR = 0x27  # 39

ADS_ADDR = 0x48  # 72
ADS_GAIN = 0
ADS_BUFFERSIZE = const(512)

ADS_ARRAY = array("h", (0 for _ in range(ADS_BUFFERSIZE)))
ADS_OFFSET = -0.006
ADS_CORRECTIONS = [
    lambda raw: (2.5270 * (10 ** -14) * raw ** 3)
    - (1.5459 * (10 ** -9) * raw ** 2)
    + (2.2487 * (10 ** -3) * raw)
    + 1.9093 * (10 ** -1)
    + ADS_OFFSET,
    lambda raw: (2.9633 * (10 ** -14) * raw ** 3)
    - (1.7011 * (10 ** -9) * raw ** 2)
    + (2.2531 * (10 ** -3) * raw)
    + 2.0171 * (10 ** -1)
    + ADS_OFFSET,
    lambda raw: (2.1699 * (10 ** -14) * raw ** 3)
    - (1.5100 * (10 ** -9) * raw ** 2)
    + (2.2491 * (10 ** -3) * raw)
    + 1.8790 * (10 ** -1)
    + ADS_OFFSET,
    lambda raw: (2.5082 * (10 ** -14) * raw ** 3)
    - (1.5100 * (10 ** -9) * raw ** 2)
    + (2.2491 * (10 ** -3) * raw)
    + 1.8790 * (10 ** -1)
    + ADS_OFFSET,
]


V_CORR = 2  # voltage correction setting

# SPI pins - SD
# bus 2 = SCK 18, CS 5, MISO 19, MOSI 23
SD_SPI_BUS = 2
SD_CS = 5


MESSAGES = {
    "init": (lambda msg, status: f"init {msg} ... {status}"),
}
