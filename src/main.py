import sys

# import _thread
from time import sleep
import uasyncio

import config as CNFG
from hardware_init import hw_init

print("\n" * 5)


class Guesstimator:
    def __init__(self):
        self.hw = hw_init()
        if self.hw:
            self.hw["lcd"].clear()
            # self.add_sw2_handlers()
        else:
            print("Hardware setup error. Exiting\n\n\n")
            sys.exit()

        # current state - meas vs setup
        self.state = "setup"
        # correction
        self.v_corr = 0

        # sd queue
        self.sd_buffer = []

        #
        self.meas_count = 0
        self.ads_buffer = CNFG.ADS_ARRAY
        self.ads = {
            "volt_adj": [0] * CNFG.CHNLS,  # empty list, 4 elements
            "raw": [0] * CNFG.CHNLS,  # empty list, 4 elements
            "avg_feed": [[] for _ in range(CNFG.CHNLS)],  # list of lists
        }
        self.volt_avg = [0] * CNFG.CHNLS

    """
    CORO 1 - measure ADC values and parse them 
    """

    async def coro_ads_measure(self):
        """measure the channels, apply corrective math and store them"""
        print("ADS_1115 measuring started")
        print(f"AVG for {CNFG.ADS_KEPT_VALUES} values with {CNFG.T_ADS_MEAS} interval")
        # continuous measuring loop feeding the data buffer with current voltage values
        while True:
            for channel in range(CNFG.CHNLS):
                # read data from the sensor
                self.ads_buffer = self.hw["ads"].read(channel1=channel)

                # log raw values
                self.ads["raw"][channel] = self.ads_buffer

                # apply third polynomial conversion and
                voltage = CNFG.ADS_CORRECTIONS[channel](self.ads_buffer)

                # add manual adjust
                self.ads["volt_adj"][channel] = voltage + self.v_corr

                # write into history buffer
                self._adc_add_hist(channel, voltage)

                # published averaged values
                self.volt_avg[channel] = self.adc_avg_hist(channel)
            await uasyncio.sleep(CNFG.T_ADS_MEAS)

    def _adc_add_hist(self, channel, voltage):
        """writes the value into historical voltage buffer while maintaining the boundaries"""
        if len(self.ads["avg_feed"][channel]) >= CNFG.ADS_KEPT_VALUES:
            _ = self.ads["avg_feed"][channel].pop(0)
        self.ads["avg_feed"][channel].append(voltage)

    def adc_avg_hist(self, channel):
        """takes the values in the channel history and returns their average"""
        if len(self.ads["avg_feed"][channel]) == 0:
            return 0
        else:
            summary = sum(self.ads["avg_feed"][channel])
            length = len(self.ads["avg_feed"][channel])
            return round(summary / length, 5)

    """
    CORO 2 - prepare data for SD queue
    """

    async def coro_data_prep(self):
        """safely access avg data, create a copy and add it to SD queue"""
        while True:
            if self.state == "meas":
                self.sd_buffer.append(self.volt_avg)
            await uasyncio.sleep(CNFG.T_CLI_PRINT_MEAS)

    """
    CORO 3 - update LCD values
    """

    async def coro_update_lcd_voltages(self):
        # self.hw["lcd"].show_cursor()
        while True:
            for row in range(0, CNFG.CHNLS):
                voltage = self.volt_avg[row]
                msg = f"{row + 1}: {voltage:05.2f} V | "
                self.hw["lcd"].move_to(0, row)
                self.hw["lcd"].putstr(msg)
            await uasyncio.sleep(CNFG.T_LCD_REFRESH)

    """
    CORO 4 - print CLI values
    """

    async def coro_update_cli_values(self):
        while True:
            if self.state == "meas":
                out = ["######"]
            else:
                out = []
            out += [f"{self.meas_count}"]
            out += [f"{v:05.2f}" for v in self.volt_avg]
            out += [str(self.v_corr)]

            print(CNFG.CSV_SPLIT.join(out))
            if self.state == "setup":
                await uasyncio.sleep(CNFG.T_CLI_PRINT_SETUP)
            else:
                await uasyncio.sleep(CNFG.T_CLI_PRINT_MEAS)

    def start(self):
        """
        coroutines
        1 - measure ADC, parse values, write last 5
        2 - prepare data in queue for LCD, CLI and SD
        3 - update LCD values
        4 - CLI value printing
        """
        print("Starting parallel execution.")
        loop = uasyncio.get_event_loop(runq_len=40, waitq_len=40)
        loop.create_task(self.coro_ads_measure())
        loop.create_task(self.coro_data_prep())
        loop.create_task(self.coro_update_lcd_voltages())
        loop.create_task(self.coro_update_cli_values())
        loop.create_task(debug())
        loop.run_forever()


async def debug():
    import gc

    while True:
        print(f"Free memory: {gc.mem_free()}")
        await uasyncio.sleep(1)


VM = Guesstimator()

# VM.measure()
VM.start()

# VM.debug()
# VM.voltage_demo()
