# ZBRQKKZ - What & Why 
Voltage logging of 4 cell accumulator pack up to 59 V, ie. 4x fully charged (14.7 V) lead acid batteries in series.
Permanent log is stored on the SD card and currently measurred values are outputted via serial.

# Operations
1. connect GND to the accumulator pack GND
2. connect lead #4 to the accumulator pack (+)  
3. connect leads #1, #2, #3 to individual cells
4. turn on the ZBRQKKZ
5. use calibrated voltmeter to measure cell #1 voltage and use potentiometer on ZBRQKKZ to adjust measured values

# Components
**Electronics**
- ESP32 + MicroPython
  - `python -m esptool --port COM12 --baud 921600 write_flash 0x1000 esp32-20210902-v1.17.bin`
- ADS 1115 ADC
  - 16 bit, 4 channel, channel V<sub>max</sub> = V<sub>dd</sub>, I2C (72 = 0x48)
  - has to be powered by 5V in our case (or voltage divider has to be adjusted)
  - we're measuring all cells against common ground and getting individual cell voltages via substraction

- SD card reader
  - SPI, picky on what SD card it accepts
  - has to be connected to VSPI (id 2, pins 18,23,19) to prevent conflict with [GPIO12 (MTDI bootstraping)](https://docs.espressif.com/projects/esp-idf/en/release-v4.0/api-reference/peripherals/sd_pullup_requirements.html#mtdi-strapping-pin)

- 4 channel voltage divider
  - reducing 0-60 V to 0-5V range
  - 110 kΩ : 10 kΩ ([Divider calc](https://ohmslawcalculator.com/voltage-divider-calculator))

**Interface**
- haptic
  - BTN1 - Power off/on
  - BTN2 - Enable/Disable SD write 
  - BTN3 - LCD backlight
  - P1 potentiometer - fine adjustment (+-0.5 V) of the measured voltage based on a manual check with calibrated multimeter
- LCD
    - I2C, 2x16 (or 20x4) chars, provides current values and instructions
- UART/Serial data line
    - to allow terminal output and logging (PuTTY). Speed: 115200
    - connected into FT232/CH430/CP2102 USB
    - RX/TX lines are opto-isolated
        - USB interface is powered from the USB hub
        - no electrical connection with the measured circuit preventing PC/laptop/USB hub from contact with the cells/pack
        - isolated by 6N137 (10 Mbit/s interface)


**Protections and power supply**
- ZBRQKKZ feeds from the measured pack. Inaccuracies introduced by this approach were evaluated as insignificant for our purpose.
- Step down (HW636) is powered from the whole pack. Death of individual cell should not affect overall operation.
- Fuse (630mA) + Zener diode (62V) connected before step down 
    - In case of overvoltage the Zener breaks and causes sufficient amperage to burn the fuse.
    - Connected before step down convertor.
- Step down is set to 5V and powers all the electronics.

 
 



# 
**Possible future features**
- replace Fuse with PTC/Polyfuse
  - suitable RC circuit would have to be designed due to slow polyfuse react times
