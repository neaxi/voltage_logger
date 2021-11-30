import machine
import uasyncio as asyncio
from aswitch import Switch


# emergency exception buffer is created to handle ISR errors
# see https://docs.micropython.org/en/latest/reference/isr_rules.html#the-emergency-exception-buffer
import micropython

micropython.alloc_emergency_exception_buf(100)

pin_btn01 = 4


def printer():
    """infinite ticking loop"""
    i = 0
    while True:
        i += 1
        print(f"{i}")
        await asyncio.sleep(1)


async def test_sw(pin):
    sw = Switch(pin)
    state = sw.switchstate
    while True:
        if sw.switchstate != state:
            print(f"Switch changed state to: {sw.switchstate}")
            state = sw.switchstate
        await asyncio.sleep(0.1)


def test_non_blocking_asyncio():
    """creates two buttons (pin 18 and 19)
    then it starts the async loop
    adds handler for both buttons in the loop
    adds tick_tock to the loop to show its running
    """
    pin4 = machine.Pin(pin_btn01, machine.Pin.IN, machine.Pin.PULL_UP)
    loop = asyncio.get_event_loop(runq_len=40, waitq_len=40)
    loop.create_task(test_sw(pin4))
    loop.create_task(printer())
    loop.run_forever()


test_non_blocking_asyncio()
