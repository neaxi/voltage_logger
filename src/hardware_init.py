from time import sleep

from machine import Pin, I2C, ADC, SPI
from primitives.switch import Switch

from circuitpython_i2c_lcd import I2cLcd
from ads1x15 import ADS1115
from sdcard import SDCard


import config as CNFG
from config import MESSAGES as MSG


def setup_i2c():
    return I2C(1, sda=Pin(CNFG.I2C_SDA), scl=Pin(CNFG.I2C_SCK), freq=CNFG.I2C_FREQ)


def setup_lcd(i2c):
    lcd = I2cLcd(i2c, CNFG.LCD_ADDR, 4, 20)
    lcd.clear()
    return lcd


def setup_ads(i2c):
    return ADS1115(i2c, CNFG.ADS_ADDR, CNFG.ADS_GAIN)


def setup_pot():
    pot = ADC(Pin(CNFG.PIN_POT))
    pot.atten(ADC.ATTN_11DB)
    return pot


def setup_sw2():
    sw_pin = Pin(CNFG.PIN_SW2, Pin.IN)
    return Switch(sw_pin)


def setup_sw_debug():
    sw_pin = Pin(CNFG.PIN_DEBUG, Pin.IN)
    return Switch(sw_pin)


def setup_sd():
    # interface - , baudrate=80000000, miso=Pin(19), mosi=Pin(23), sck=Pin(18))
    spisd = SPI(CNFG.SD_SPI_BUS)
    spisd.init()
    sd = SDCard(spisd, Pin(CNFG.SD_CS))

    return sd


def print_status_on_lcd(lcd, msg):
    lcd.putstr(f"{msg}\n")
    msg = msg.replace(" ...", "\t...")


def hw_init():
    devices = {}
    master_fail_flag = False
    try:
        i2c = setup_i2c()
        print(f"I2C OK - visible devices: {i2c.scan()}")
    except BaseException as err:
        print("I2C setup failed")
        master_fail_flag = True

    peripheries = [
        ("lcd", setup_lcd, "LCD"),
        ("ads", setup_ads, "ADS"),
        ("pot", setup_pot, "POT"),
        ("sw2", setup_sw2, "SW2"),
        ("sw_d", setup_sw_debug, "SW_D"),
        ("sd", setup_sd, "SD"),
    ]

    for p in peripheries:
        # p[0] = id
        # p[1] = assoc setup function
        # p[2] = user friendly name
        fail = False
        e_init = ""
        try:
            if p[0] == "lcd" or p[0] == "ads":
                # lcd and ads functions needs the I2C bus object
                devices[p[0]] = p[1](i2c)
            else:
                # SD, POT, SW2 - func requires no arg
                devices[p[0]] = p[1]()
        except BaseException as err:
            e_init = err
            fail = True
            if p[0] != "sd":
                master_fail_flag = True
            else:
                # if the SD is the only one which failed, continue
                # we can boot up without SD
                devices[p[0]] = None

        if fail:
            msg = MSG["init"](p[2], "FAIL")
            print(f"{p[2]} failed on INIT. Exception details: {e_init}")
        else:
            msg = MSG["init"](p[2], "OK")
            print(msg)
        if "lcd" in devices:
            print_status_on_lcd(devices["lcd"], f"{msg: <20s}")

        sleep(0.5)

    sleep(2)

    if master_fail_flag:
        return None

    return devices


if __name__ == "__main__":
    hw_init()
