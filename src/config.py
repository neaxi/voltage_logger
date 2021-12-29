from array import array

# amount of channels ... not really needed to be changed, but kept in CONST to have every magic number in one place
CHNLS = 4

# SPI pins - SD
# bus 2 = SCK 18, CS 5, MISO 19, MOSI 23
SD_SPI_BUS = 2
SD_CS = 5
SD_MNT = "/sda"
SD_FILE_PREFIX = r"measure_"
SD_FILE_HEADER = ["Time", "#", "CH 1", "CH 2", "CH 3", "CH 4"]

CSV_SPLIT = ";"  # used to split SD saved values
CLI_SPLIT = "\t"  # used to split values printed on the screen

T_ADS_MEAS = 0.5  # how often is the ADC sampled
T_LCD_REFRESH = 1  # updating LCD values
T_CLI_PRINT_SETUP = 2  # used for setting up the correction
T_CLI_PRINT_MEAS = 20  # slower, console log flood prevention
T_SD_WRITE = 120  # how often perform SD write

# potentiometer and SW2 pins
PIN_SW2 = 34
PIN_DEBUG = 35

PIN_POT = 33
V_CORR = 2  # voltage correction setting
V_CORR_STEP = 0.05 * 100  # don't change the * 100, 2 digits float workaround

# i2c bus pins - ADC, LCD
I2C_SDA = 21
I2C_SCK = 22
I2C_FREQ = 400000

LCD_ADDR = 0x27  # 39

ADS_ADDR = 0x48  # 72
ADS_GAIN = 0
ADS_BUFFERSIZE = const(512)
ADS_KEPT_VALUES = 5  # how many past measurements are we keeping

ADS_ARRAY = array("h", (0 for _ in range(ADS_BUFFERSIZE)))
ADS_OFFSET = 0.0018  # balanced through calib spreadsheet
ADS_MAGIC = 0  # if additional non deterministic magic is required
ADS_CORRECTIONS = [
    lambda raw: -(1.2028 * (10 ** -14) * raw ** 3)
    + (6.6834 * (10 ** -10) * raw ** 2)
    + (2.2315 * (10 ** -3) * raw)
    + 1.4131 * (10 ** -1)
    + ADS_OFFSET,
    lambda raw: -(1.587 * (10 ** -14) * raw ** 3)
    + (1.0182 * (10 ** -9) * raw ** 2)
    + (2.2270 * (10 ** -3) * raw)
    + 1.893 * (10 ** -1)
    + ADS_OFFSET,
    lambda raw: -(3.9360 * (10 ** -15) * raw ** 3)
    + (3.0906 * (10 ** -10) * raw ** 2)
    + (2.2384 * (10 ** -3) * raw)
    + 1.2621 * (10 ** -1)
    + ADS_OFFSET,
    lambda raw: -(5.5219 * (10 ** -15) * raw ** 3)
    + (4.1715 * (10 ** -10) * raw ** 2)
    + (2.2351 * (10 ** -3) * raw)
    + 1.3192 * (10 ** -1)
    + ADS_OFFSET,
]


MESSAGES = {
    "init": (lambda dev, status: f"init {dev} ... {status}"),
}
