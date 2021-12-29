"""
https://learn.adafruit.com/micropython-hardware-sd-cards/micropython
https://docs.micropython.org/en/latest/library/machine.SDCard.html
https://techtotinker.blogspot.com/2021/04/023-esp32-micropython-how-to-use-sd.html

Board ground (GND) to microSD breakout ground (GND).
Board 3.3V power to microSD breakout 3.3V power.
Board SPI CLK (ESP8266 GPIO 14) to microSD breakout clock (CLK).
Board SPI MOSI (ESP8266 GPIO 13) to microSD breakout data input (DI).
Board SPI MISO (ESP8266 GPIO 12) to microSD breakout data output (DO).
Board GPIO 15 (or any other free digital IO pin) to microSD breakout chip select (CS).
"""

from machine import Pin, SPI  # SoftSPI
import os
from sdcard import SDCard

spisd = SPI(2)  # , baudrate=80000000, miso=Pin(19), mosi=Pin(23), sck=Pin(18))
spisd.init()
sd = SDCard(spisd, Pin(5))
# os.VfsFat.mkfs(sd)
# vfs = os.VfsFat(sd)
os.mount(sd, "/sda")
print(os.listdir("/sda"))
with open("/sda/test.txt", "a") as fp:
    for idx in range(0, 1000):
        print(f"writing {idx}")
        fp.write(f"{idx}\n")

os.umount("/sda")
