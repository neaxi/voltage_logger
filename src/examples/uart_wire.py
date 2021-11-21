from time import sleep
from machine import UART


# UART 1
# TX = GPIO 10 = D3
# RX = GPIO 09 = D2

uart = UART(1, 115200)
uart.init(115200, bits=8, parity=None, stop=1)

i = 0
while True:
    print(i)
    uart.write("{}\r\n".format(i))
    i += 1
    sleep(0.1)

    # uart.read()
