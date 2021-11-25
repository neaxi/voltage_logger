import sys
import _thread
from time import sleep
import config as CNFG
from hardware_init import hw_init

print("\n" * 5)


class Guesstimator:
    def __init__(self):
        hw = hw_init()
        if hw:
            self.hw = hw
        else:
            print("Hardware setup error. Exiting\n\n\n")
            sys.exit()

        self.ads_buffer = CNFG.ADS_ARRAY
        self.data = {
            "adc_voltage": [0] * 4,  # empty list, 4 elements
            "adc_raw": [0] * 4,  # empty list, 4 elements
            "ads_hist": [[] for _ in range(CNFG.ADS_KEPT_VALUES)],  # list of lists
            "pot": 0,
        }
        self.flag_measure = True
        self.flag_display = True
        self.flag_sd_write = False
        self.state = "setup"

    def _adc_add_hist(self, channel, voltage):
        """writes the value into historical voltage buffer while maintaining the boundaries"""
        if len(self.data["ads_hist"][channel]) >= CNFG.ADS_KEPT_VALUES:
            _ = self.data["ads_hist"][channel].pop(0)
        self.data["ads_hist"][channel].append(voltage)

    def adc_avg_hist(self, channel):
        """takes the values in the channel history and returns their average"""
        if len(self.data["ads_hist"][channel]) == 0:
            return 0
        else:
            return sum(self.data["ads_hist"][channel]) / len(
                self.data["ads_hist"][channel]
            )

    def measure_ads(self):
        """measure the channels, apply corrective math and store them"""
        for channel in range(4):
            # read data from the sensor
            self.ads_buffer = self.hw["ads"].read(channel1=channel)
            # log raw values
            self.data["adc_raw"][channel] = self.ads_buffer
            # apply third polynomial conversion
            voltage = CNFG.ADS_CORRECTIONS[channel](self.ads_buffer)
            # add manual adjust
            self.data["adc_voltage"][channel] = voltage + self.data["pot"]
            # write into history buffer
            self._adc_add_hist(channel, voltage)

    def measure_pot(self):
        # read pot, map the 4096 values on range 0-V_CORR and substract half to have 0 in middle of the interval
        self.data["pot"] = round(
            self.hw["pot"].read() / 4096 * CNFG.V_CORR - CNFG.V_CORR / 2, 2
        )

    """
    def measure(self):
        self.measure_ads()
        self.measure_pot() 
    """

    def update_cli_values(self):
        out = []
        for channel in range(4):
            out.append(f"{self.adc_avg_hist(channel):05.2f}")
            # [f"{v:05.2f}" for v in self.data["adc_voltage"]]
        # out = [str(v) for v in self.data["adc_raw"]]  # DEBUG to print RAW ADC values to serial
        out += [str(self.data["pot"])]
        print(CNFG.CSV_SPLIT.join(out))

    def update_lcd_voltages(self):
        # self.hw["lcd"].show_cursor()
        # self.hw["lcd"].clear()
        for row in range(0, 4):
            # voltage = self.data["adc_voltage"][row]
            voltage = self.data["adc_voltage"][row]
            msg = f"{row + 1}: {voltage:05.2f} V | "
            self.hw["lcd"].move_to(0, row)
            self.hw["lcd"].putstr(msg)

    def sd_mount(self):
        ...

    def sd_umount(self):
        ...

    def t_adc_meas(self):
        print("ADS_1115 measuring thread started")
        print(f"AVG for {CNFG.ADS_KEPT_VALUES} values with {CNFG.T_ADS_MEAS} interval")
        # continuous measuring loop feeding the data buffer with current voltage values
        while self.flag_measure:
            self.measure_ads()
            sleep(CNFG.T_ADS_MEAS)

    def t_user_display(self):
        while self.flag_display:
            self.update_lcd_voltages()
            self.update_cli_values()
            if self.state == "measuring":
                sleep(CNFG.T_LCD_REFRESH_MEAS)
            else:
                sleep(CNFG.T_LCD_REFRESH_SETUP)

    def start(self):
        """
        thread 1 - measure the ADC every 0.2 sec
        thread 2 - update LCD for the user
        """
        print("Starting threads.")
        _thread.start_new_thread(self.t_adc_meas, ())
        _thread.start_new_thread(self.t_user_display())


VM = Guesstimator()

# VM.measure()
# VM.start()

# VM.debug()
# VM.voltage_demo()
sleep(CNFG.T_LCD_REFRESH_SETUP)
