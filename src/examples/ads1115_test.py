# main.py

from machine import Pin, SoftI2C
from array import array
from time import sleep
import ads1x15

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
i2c.scan()

addr = 72
gain = 0
_BUFFERSIZE = const(512)
data = array("h", (0 for _ in range(_BUFFERSIZE)))
ads = ads1x15.ADS1115(i2c, addr, gain)

while True:
    data = ads.read()
    print(
        "Raw {}\t\tCustom {:.4f}\t\tBuilt-in  {:.4f}".format(
            data, data * 6.144 / 32768, ads.raw_to_v(data)
        )
    )
    sleep(0.1)
