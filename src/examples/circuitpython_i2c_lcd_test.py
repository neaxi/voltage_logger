"""Implements a HD44780 character LCD connected via PCF8574 on I2C in CircuitPython.
   Author https://github.com/dhylands/python_lcd """


from machine import I2C, Pin
from time import sleep
from circuitpython_i2c_lcd import I2cLcd
import random

# The PCF8574 has a jumper selectable address: 0x20 - 0x27
DEFAULT_I2C_ADDR = 0x27


batt_anim = [
    bytearray([0x0E, 0x1B, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1F]),  # 0% Empty
    bytearray([0x0E, 0x1B, 0x11, 0x11, 0x11, 0x11, 0x1F, 0x1F]),  # 16%
    bytearray([0x0E, 0x1B, 0x11, 0x11, 0x11, 0x1F, 0x1F, 0x1F]),  # 33%
    bytearray([0x0E, 0x1B, 0x11, 0x11, 0x1F, 0x1F, 0x1F, 0x1F]),  # 50%
    bytearray([0x0E, 0x1B, 0x11, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F]),  # 66%
    bytearray([0x0E, 0x1B, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F]),  # 83%
    bytearray([0x0E, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F]),  # 100% Full
    bytearray([0x0E, 0x1F, 0x1B, 0x1B, 0x1B, 0x1F, 0x1B, 0x1F]),  # ! Error
]


i2c = I2C(1, sda=Pin(21), scl=Pin(22), freq=400000)

# 2 lines, 16 characters per line
lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 4, 20)

static = ["ZBRQKKZ", "tester", "", "RNG demo"]


def voltage_demo():
    lcd.show_cursor()
    while True:
        lcd.clear()
        for i in range(0, 4):
            voltage = random.randint(0, 500) / 100
            msg = "{}: {:0.2f} V | {:^8}".format(i + 1, voltage, static[i])
            lcd.move_to(0, i)
            lcd.putstr(msg)
        sleep(5)


voltage_demo()


def test_main():
    """Test function for verifying basic functionality."""
    print("Running test_main")

    # custom chars
    bell = bytearray([0x04, 0x0E, 0x0E, 0x0E, 0x1F, 0x00, 0x04, 0x00])
    note = bytearray([0x02, 0x03, 0x02, 0x0E, 0x1E, 0x0C, 0x00, 0x00])
    clock = bytearray([0x00, 0x0E, 0x15, 0x17, 0x11, 0x0E, 0x00, 0x00])
    heart = bytearray([0x00, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x00, 0x00])
    duck = bytearray([0x00, 0x0C, 0x1D, 0x0F, 0x0F, 0x06, 0x00, 0x00])
    check = bytearray([0x00, 0x01, 0x03, 0x16, 0x1C, 0x08, 0x00, 0x00])
    cross = bytearray([0x00, 0x1B, 0x0E, 0x04, 0x0E, 0x1B, 0x00, 0x00])
    retarrow = bytearray([0x01, 0x01, 0x05, 0x09, 0x1F, 0x08, 0x04, 0x00])
    lcd.custom_char(0, bell)
    lcd.custom_char(1, note)
    lcd.custom_char(2, clock)
    lcd.custom_char(3, heart)
    lcd.custom_char(4, duck)
    lcd.custom_char(5, check)
    lcd.custom_char(6, cross)
    lcd.custom_char(7, retarrow)

    lcd.custom_char(0, batt_anim[0])
    for i in range(0, 40):
        lcd.putchar(chr(0))
        lcd.putchar(" ")
    while True:
        for i in range(0, len(batt_anim)):
            lcd.custom_char(0, batt_anim[i])
            sleep(0.3)

    return ()

    lcd.putstr("It works!\nSecond line\nThird line\nFourth line")
    sleep(10)
    lcd.clear()
    lcd.putstr("Custom chars:\n")
    for i in range(7):
        lcd.putchar(" ")
        lcd.putchar(chr(i))
        sleep(1)

    sleep(30)
    lcd.clear()
    count = 0

    while True:
        lcd.move_to(0, 0)
        count += 1
        if count % 10 == 3:
            print("Turning backlight off")
            lcd.backlight_off()
        if count % 10 == 4:
            print("Turning backlight on")
            lcd.backlight_on()
        if count % 10 == 5:
            print("Turning display off")
            lcd.display_off()
        if count % 10 == 6:
            print("Turning display on")
        if count % 10 == 7:
            print("Turning display & backlight off")
            lcd.backlight_off()
            lcd.display_off()
        if count % 10 == 8:
            print("Turning display & backlight back on")
            lcd.backlight_on()
            lcd.display_on()


# if __name__ == "__main__":
test_main()
