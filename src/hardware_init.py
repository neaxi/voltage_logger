import config as CNFG
from config import MESSAGES as MSG
from machine import Pin, I2C, ADC, SPI
from array import array
import os
from time import sleep

from circuitpython_i2c_lcd import I2cLcd
from ads1x15 import ADS1115
from sdcard import SDCard


def setup_i2c():
    return I2C(1, sda=Pin(CNFG.I2C_SDA), scl=Pin(CNFG.I2C_SCK), freq=CNFG.I2C_FREQ)


def setup_lcd(i2c):
    lcd = I2cLcd(i2c, CNFG.LCD_ADDR, 4, 20)
    lcd.clear()
    return lcd


def setup_ads(i2c):
    return ADS1115(i2c, CNFG.ADS_ADDR, CNFG.ADS_GAIN)


def setup_pot():
    pot = ADC(Pin(32))
    pot.atten(ADC.ATTN_11DB)
    return pot


def setup_sw2():
    return Pin(2, Pin.IN)


def setup_sd():
    # interface - , baudrate=80000000, miso=Pin(19), mosi=Pin(23), sck=Pin(18))
    spisd = SPI(CNFG.SD_SPI_BUS)
    spisd.init()
    # storage
    sd = SDCard(spisd, Pin(CNFG.SD_CS))
    vfs = os.VfsFat(sd)
    # os.mount(vfs, "/sda")
    # print(os.listdir("/sda"))
    # os.umount("/sda")

    return sd


def print_status(lcd, msg):
    lcd.putstr(f"{msg}\n")
    msg = msg.replace(" ...", "\t...")
    print(msg)


def hw_init():
    devices = {}
    fail_flag = False
    i2c = setup_i2c()

    peripheries = [
        ("lcd", setup_lcd, "LCD"),
        ("ads", setup_ads, "ADS"),
        ("sd", setup_sd, "SD"),
        ("pot", setup_pot, "POT"),
        ("sw2", setup_sw2, "SW2"),
    ]

    for p in peripheries:
        try:
            if p[0] == "lcd" or p[0] == "ads":
                devices[p[0]] = p[1](i2c)
            else:
                # SD, POT, SW2
                devices[p[0]] = p[1]()
            print_status(devices["lcd"], MSG["init"](p[2], "OK"))
        except BaseException as err:
            print_status(devices["lcd"], MSG["init"](p[2], "FAIL"))
            print(err)
            fail_flag = True
        sleep(0.5)

    sleep(2)
    if fail_flag:
        return None
    else:
        return devices


if __name__ == "__main__":
    hw_init()
