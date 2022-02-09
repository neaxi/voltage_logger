import sys
import os
import math
import re
import time
import uasyncio

import config as CNFG
from hardware_init import hw_init, setup_sd

print("\n" * 5)


def timestr():
    t = time.localtime()
    return f"{t[3]:02}:{t[4]:02}:{t[5]:02}"


class Guesstimator:
    def __init__(self):
        self.hw = hw_init()
        if self.hw:
            self.hw["lcd"].clear()
            self._add_switch_handlers()

        else:
            print("Hardware setup error. Exiting\n\n\n")
            sys.exit()

        # current state - meas vs setup
        self.meas = False
        self.debug = False
        self.target_file = None
        # correction
        self.v_corr = 0

        # sd queue
        self.sd_buffer = []

        self.lcd_messages = [""] * 4
        # default LCD values after boot
        self.lcd_messages[2] = "SD: ???"
        self.lcd_messages[3] = "setup"

        # measurement variables
        self.meas_count = 0
        self.ads_buffer = CNFG.ADS_ARRAY
        self.ads = {
            # voltages converted from raw after corrections/adjustment
            "volt_adj": [0] * CNFG.CHNLS,  # empty list, 4 elements
            # raw valueas as measured by the ADC
            "raw": [0] * CNFG.CHNLS,  # empty list, 4 elements
            # holds historical data from which averages are computed
            "avg_feed": [[] for _ in range(CNFG.CHNLS)],  # list of lists
            # average values computed from the feed, ready to be printed out
            "avg_print": [0] * CNFG.CHNLS,
        }

    def _add_switch_handlers(self):
        self.hw["sw2"].open_func(self.sw2_meas, (False,))
        self.hw["sw2"].close_func(self.sw2_meas, (True,))
        self.hw["sw_d"].open_func(self.sw_debug, (False,))
        self.hw["sw_d"].close_func(self.sw_debug, (True,))

    def sd_fail(self, msg):
        print(msg)
        self.lcd_messages[2] = "SD ERROR"
        print("Attempting to remount SD card")
        try:
            self.hw["sd"] = setup_sd()
        except OSError:
            print("Remount failed.")

    #
    # CORO 1 - measure ADC values and parse them
    #

    async def coro_ads_measure(self):
        """measure the channels, apply corrective math and store them"""
        print("ADS_1115 measuring started")
        print(
            f"Average for {CNFG.ADS_KEPT_VALUES} values with {CNFG.T_ADS_MEAS} interval"
        )
        # continuous measuring loop feeding the data buffer with current voltage values
        while True:
            for channel in range(CNFG.CHNLS):
                # read data from the sensor
                self.ads_buffer = self.hw["ads"].read(channel1=channel)

                # log raw values
                self.ads["raw"][channel] = self.ads_buffer

                # apply third polynomial conversion and
                voltage = CNFG.ADS_CORRECTIONS[channel](self.ads_buffer)
                # add manual adjust and possibly a magic number
                self.ads["volt_adj"][channel] = voltage + self.v_corr + CNFG.ADS_MAGIC

            # perform subtractions - must be performed after all the channels are known
            self.ads["sub"] = self.ads_subtract(self.ads["volt_adj"])

            for channel in range(CNFG.CHNLS):
                # write processed sub(raw + corr + adj) values into history buffer
                self._adc_add_hist(channel, self.ads["sub"][channel])

                # publish averaged values
                self.ads["avg_print"][channel] = self.adc_avg_hist(channel)
            await uasyncio.sleep(CNFG.T_ADS_MEAS)

    def ads_subtract(self, v):
        meas = list(v)  # temporary list for processing
        final = [0] * CNFG.CHNLS
        buffer = []
        # figure out the channel order
        # processed items are max'd by CNFG.TMAX CONST
        while sum(meas) != CNFG.CHNLS * CNFG.TMAX:
            # find minimum value + its position and store them
            idx = meas.index(min(meas))
            volts = meas[idx] if meas[idx] > 1 else 0
            buffer.append((idx, volts))
            # max the item we've already processed so it won't get picked by min()
            # can't use del() or pop() as it would shift the indexes
            meas[idx] = CNFG.TMAX

        # go through values and subtract sum of the previous/smaller measurements
        for idx, m in enumerate(buffer):
            if idx == 0:
                # first one is the smallest = no subtraction
                final[m[0]] = m[1]
            elif (
                buffer[idx - 1][1] >= m[1] - CNFG.TOLER
                and buffer[idx - 1][1] <= m[1] + CNFG.TOLER
            ):
                # probes most likely on the same wire or the battery died
                # ie +- the same voltage as previous
                # zero out the previous value to have the common on the highest channel number
                final[m[0] - 1] = 0
                final[m[0]] = m[1] - sum(final)
            else:
                # with each higher number we subtract sum of all the previous
                final[m[0]] = m[1] - sum(final)
        del v, buffer  # cleanup
        return final

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

    #
    # CORO 2 - prepare data for SD queue
    #

    async def coro_data_prep(self):
        """safely access avg data, create a copy and add it to SD queue"""
        while True:
            if self.meas:
                self.sd_buffer.append(
                    [timestr(), self.meas_count] + self.ads["avg_print"]
                )
            await uasyncio.sleep(CNFG.T_CLI_PRINT_MEAS)

    #
    # CORO 3 - LCD
    #
    def lcd_message(self):
        # ensure string is not longer than 8, if shorter pad to 8 places, align right
        for line, msg in enumerate(self.lcd_messages):
            fmt = lambda m: f"{m: >8.8s}"
            self.hw["lcd"].move_to(12, line)
            self.hw["lcd"].putstr(fmt(msg))

    async def coro_update_lcd_voltages(self):
        if self.debug:
            self.hw["lcd"].show_cursor()
        while True:
            for row in range(0, CNFG.CHNLS):
                if self.debug:
                    # show me the raw voltages for debugging
                    voltage = self.ads["volt_adj"][row]
                else:
                    # otherwise subtracted only
                    voltage = self.ads["sub"][row]

                msg = f"{row + 1}: {voltage:05.2f} V |"
                self.hw["lcd"].move_to(0, row)
                self.hw["lcd"].putstr(msg)

            # update LCD texts
            self.lcd_messages[0] = timestr()
            if not self.hw["sd"] and not self.lcd_messages[2]:
                self.lcd_messages[2] = "No SD"
            self.lcd_message()
            await uasyncio.sleep(CNFG.T_LCD_REFRESH)

    #
    # CORO 4 - print CLI values
    #
    def debug_print(self):
        # print(self.ads)
        # print(self.lcd_messages)
        pass

    async def coro_update_cli_values(self):
        while True:
            if self.meas:
                out = ["######", timestr()]
                self.meas_count += 1
                # workaround for power debugging ... return averages once done
                data = self.ads["avg_print"]
            else:
                out = []
                # show real time values during setup
                data = self.ads["sub"]
                if self.debug:
                    data += self.ads["volt_adj"]
            out += [f"{self.meas_count}"]
            out += [f"{v:05.2f}" for v in data]
            out += [str(self.v_corr)]

            # print debug data
            if self.debug:
                self.debug_print()

            print(CNFG.CLI_SPLIT.join(out))
            # throw away the list after printing it
            del data, out

            if self.meas:
                await uasyncio.sleep(CNFG.T_CLI_PRINT_MEAS)
            else:
                await uasyncio.sleep(CNFG.T_CLI_PRINT_SETUP)

    #
    # CORO 5 - POT and Switches
    # switches are called from their respectiva handlers
    #
    async def sw_debug(self, state):
        if state and self.meas:
            print("Debug not allowed in Measurement mode")
        elif state:
            print("Debug mode turned on")
            self.debug = True
            self.lcd_messages[3] = "DEBUG!!"
        elif not state and not self.debug:
            # switched got opened, but we were not in debug anyway
            pass
        else:
            self.debug = False
            print("Debug mode turned off")
            self.lcd_messages[3] = "setup"

    async def sw2_meas(self, state):
        if state:
            st = "closed"
            self.meas = True
            self.sd_mount()
            print("MEASUREMENT: displaying average (AVG) values")
            print(f"MEASUREMENT: interval {CNFG.T_CLI_PRINT_MEAS} sec")
            print(f"MEASUREMENT: saving data to SD every {CNFG.T_SD_WRITE} sec")
            self.lcd_messages[3] = "measure"
        else:
            st = "opened"
            self.meas = False
            self.meas_count = 0
            # dump any measurement left in a buffer prior umount
            self.dump_buffer_to_sd()
            self.sd_umount()
            print("SETUP: displaying real time values")
            self.lcd_messages[3] = "setup"
        print(f"Switch SW2 is {st}; Meas state {self.meas}")

    async def coro_measure_pot(self):
        """read pot, map the 4096 values on range 0-V_CORR, round to 2 places
        substract half of V_CORR to have 0 in middle of the interval
        adjust to the "step value" via ceiling
        *100 and /100 operations added to avoid ceiling over float numbers
        """
        ceil = lambda x, y: math.ceil(x * (1.0 / y)) / (1.0 / y)
        while True:
            val = self.hw["pot"].read()
            v_mapped = (round(val / 4096 * CNFG.V_CORR, 2) - CNFG.V_CORR / 2) * 100
            # -1 * introduced to have positive values on the right side of the pot
            self.v_corr = -1 * ceil(v_mapped, CNFG.V_CORR_STEP) / 100
            self.lcd_messages[1] = f"C: {self.v_corr:5.2f}"
            await uasyncio.sleep(CNFG.T_ADS_MEAS)

    #
    # CORO 6 - SD card operations
    #

    def set_target_meas_file(self):
        print(f"Current SD Card files: {os.listdir(CNFG.SD_MNT)}")
        files = os.listdir(CNFG.SD_MNT)
        # filter measurement files only
        filtered = list(filter(re.compile(CNFG.SD_FILE_PREFIX).match, files))
        if not filtered:
            self.target_file = f"{CNFG.SD_FILE_PREFIX}0000.csv"
        else:
            # find the highest number
            maxint = max(map(int, [c.split("_")[1].split(".")[0] for c in filtered]))
            self.target_file = f"{CNFG.SD_FILE_PREFIX}{maxint + 1:04d}.csv"

    def sd_mount(self):
        try:
            if not self.hw["sd"]:
                self.sd_fail("Trying to init SD card again.")

            print(f"Mounting SD to {CNFG.SD_MNT}")
            vfs = os.VfsFat(self.hw["sd"])
            os.mount(vfs, CNFG.SD_MNT)

            self.set_target_meas_file()
            print(f"Will be writting to {self.target_file}")
            # write header of the table into target
            with open(f"{CNFG.SD_MNT}/{self.target_file}", "a") as fp:
                fp.write(f"{CNFG.CSV_SPLIT.join(CNFG.SD_FILE_HEADER)}\n")
            self.lcd_messages[2] = "SD READY"

        except BaseException as err:
            self.sd_fail(f"!!! SD MOUNT FAILED:\n{err}")

    def sd_umount(self):
        print(f"Umounting SD from {CNFG.SD_MNT}")
        try:
            # os.path not available in micropython
            os.umount(CNFG.SD_MNT)
            self.target_file = None
        except BaseException as err:
            self.sd_fail(f"Umount failed:\n{err}")

    def dump_buffer_to_sd(self):
        if self.target_file:
            print(f"Writing to SD. Total entries: {len(self.sd_buffer)}")
            self.lcd_messages[2] = "SD WRITE"
            try:
                with open(f"{CNFG.SD_MNT}/{self.target_file}", "a") as fp:
                    for _ in range(len(self.sd_buffer)):
                        # accessed via range instead of directly
                        # a) to prevent access on object being changed
                        # b) we're always poping index [0]
                        out = map(str, self.sd_buffer.pop(0))
                        fp.write(f"{CNFG.CSV_SPLIT.join(out)}\n")
                print("SD write complete.")
                self.lcd_messages[2] = "SD READY"
            except BaseException as err:
                self.sd_fail(f"SD write failed:\n{err}")

    async def sd_writer(self):
        while True:
            if self.meas:
                self.dump_buffer_to_sd()
            await uasyncio.sleep(CNFG.T_SD_WRITE)

    def start(self):
        """
        coroutines
        1 - measure ADC, parse values, write last 5
        2 - prepare data in queue for LCD, CLI and SD
        3 - update LCD values
        4 - CLI value printing
        5 - monitor POT and SW2
        6 - SD writing coro
        """
        print("Starting parallel execution.")
        loop = uasyncio.get_event_loop(runq_len=40, waitq_len=40)
        loop.create_task(self.coro_ads_measure())
        loop.create_task(self.coro_data_prep())
        loop.create_task(self.coro_update_lcd_voltages())
        loop.create_task(self.coro_update_cli_values())
        loop.create_task(self.coro_measure_pot())
        loop.create_task(self.sd_writer())
        loop.run_forever()


if __name__ == "__main__":
    VM = Guesstimator()
    VM.start()
