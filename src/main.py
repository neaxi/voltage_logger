import config as CNFG

from config import MESSAGES as MSG
from time import sleep
from sys import exit
from hardware_init import hw_init

print("\n" * 5)


class Guesstimator:
    def __init__(self):
        hw = hw_init()
        if hw:
            self.hw = hw
        else:
            print("Hardware setup error. Exiting\n\n\n")
            exit()

        self.ads_buffer = CNFG.ADS_ARRAY
        self.data = {
            "adc_voltage": [0] * 4,  # empty list, 4 elements
            "adc_raw": [0] * 4,  # empty list, 4 elements
            "pot": 0,
        }

    def measure_ads(self):
        for channel in range(0, 4):
            # read data from the sensor
            self.ads_buffer = self.hw["ads"].read(channel1=channel)
            # log raw values
            self.data["adc_raw"][channel] = self.ads_buffer
            # apply third polynomial conversion
            voltage = CNFG.ADS_CORRECTIONS[channel](self.ads_buffer)
            # add manual adjust
            self.data["adc_voltage"][channel] = voltage + self.data["pot"]

    def measure_pot(self):
        # read pot, map the 4096 values on range 0-V_CORR and substract half to have 0 in middle of the interval
        self.data["pot"] = round(
            self.hw["pot"].read() / 4096 * CNFG.V_CORR - CNFG.V_CORR / 2, 2
        )

    def measure(self):
        self.measure_ads()
        self.measure_pot()

    def debug(self):
        out = [f"{v:05.2f}" for v in self.data["adc_voltage"]]
        # out = [str(v) for v in self.data["adc_raw"]]  # DEBUG to print RAW ADC values to serial
        out += [str(self.data["pot"])]
        print(CNFG.CSV_SPLIT.join(out))

    def voltage_demo(self):
        # self.hw["lcd"].show_cursor()
        # self.hw["lcd"].clear()
        for row in range(0, 4):
            voltage = self.data["adc_voltage"][row]
            msg = "{}: {:05.2f} V | {:^8}".format(
                row + 1, voltage, "<" + "-" * (row + 1)
            )
            self.hw["lcd"].move_to(0, row)
            self.hw["lcd"].putstr(msg)

    def sd_mount():
        ...

    def sd_umount():
        ...


VM = Guesstimator()

while True:
    VM.measure()
    VM.debug()
    VM.voltage_demo()
    sleep(CNFG.T_LCD_REFRESH_SETUP)
