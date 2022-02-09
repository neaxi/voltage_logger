# Voltage logger
CS50 Video demo: https://youtu.be/C_FzpJQzrRs
    
    

# What & Why 
Our goal is to have graphable discharge data when load testing UPS batteries. Target UPS systems for this project are using max. 4 batteries configuration (like APC RBC25), so the whole design is affected by this cap.  
Therefore, we're performing voltage logging of accumulator pack up to 59 V, ie. 4x fully charged Pb or LiFePo4 batteries in a series.  
Permanent log (.csv) is stored on the SD card and currently measurred values are available via serial interface (microUSB).

# Operations
**Usage**
1. connect GND to the accumulator pack GND
2. connect lead #4 to the accumulator pack (+)  
3. connect leads #1, #2, #3 to individual cells
4. turn on the logger via PWR switch
    - the logger will always start in "setup" mode
5. use calibrated voltmeter to measure cell #1 voltage and use calibration potentiometer on the logger to adjust measured values
6. flip the SD switch into (1), to enter the "measurement" mode
    - different time intervals
    - SD card logging

**Timing**
- 0.5 s - ADS sampling
- 1 s - LCD refresh
- 2 s - CLI printout in "setup" mode
- 20 s - CLI printout in "measurement" mode
- 120 s - interval with which the data are written on the SD card

# Technical
**Electronics**
- ESP32 + [MicroPython](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html)
  - `python -m esptool --port COM12 --baud 921600 write_flash 0x1000 esp32-20210902-v1.17.bin`
- ADS 1115 ADC
  - 16 bit, 4 channel, channel V<sub>max</sub> = V<sub>dd</sub>, I2C (72 = 0x48)
  - has to be powered by 5V in our case (or voltage divider has to be adjusted)
  - we're measuring all cells against common ground and getting individual cell voltages via subtraction
  - by default the measured voltage is obtained by `RAW * 6.144 / 32768` (`6.144` is the gain; `32768` is the 2^16 range). The transformation is included into polynomial correction formulas in our case. Calibration measurements are available in the documentation.
  - ADC GND is connected to "both" grounds - power source GND and step down GND
    - this partially bypasses the power switch as even when turned off the power buss for digital part has active voltage, but low enough to avoid activating anything
    - V<sub>src</sub> -> V<sub>pwrbus</sub>: 57 V -> 0.83 V; 30 V -> 0.48 V; 10 V -> 0.07 V
  - **Calibration**
    - ADC raw value measurements were taken for each channel on 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 58 volts.
    - third-degree polynominal formulas were derived from the measurements and are being applied on the values reported by the ADC to get better precision (absolute deviation below 0.05 V)
    - offset is also added to the measured value to ensure deviation is symmetrical/centered around the real value


- SD card reader
  - SPI, reader is picky on what SD card it accepts
    - user is notified if the logger can't write on the SD
  - has to be connected to VSPI (id 2, pins 18,23,19) to prevent conflict with [GPIO12 (MTDI bootstraping)](https://docs.espressif.com/projects/esp-idf/en/release-v4.0/api-reference/peripherals/sd_pullup_requirements.html#mtdi-strapping-pin)
  - data are buffered and written based on time interval to prevent excesive writes with each individual measurement  

  
- 4 channel voltage divider
  - reducing 0-60 V to 0-5V range
  - 110 kΩ : 10 kΩ ([Divider calc](https://ohmslawcalculator.com/voltage-divider-calculator))

**Interface**
- haptic
  - BTN1 - Power off/on
  - BTN2 - Enable/Disable SD write 
  - P1 potentiometer - fine adjustment (+-0.5 V range; 0.1 V steps) of the measured voltage based on a manual check with calibrated multimeter
- LCD
    - I2C, 2x16 (or 20x4) chars, provides current values and instructions
    - 20x4:
        - default I2C address = 39 (0x27)
    - custom LCD char guide https://clach04.github.io/lcdchargen/
        
- UART/Serial data line
    - to allow terminal output and logging (PuTTY). Speed: 115200
    - connected into FT232/CH430/CP2102 USB
    - RX/TX lines are opto-isolated
        - USB interface is powered from the USB hub
        - no electrical connection with the measured circuit preventing PC/laptop/USB hub from contact with the cells/pack
        - isolated by 6N137 (10 Mbit/s interface)


**Protections and power supply**
- The logger feeds from the measured pack. Inaccuracies introduced by this approach were evaluated as insignificant for our purpose (17 mA draw on average).
- Step down (H6201 based?) is powered from the whole pack/highest voltage. Death of individual cell should not affect overall operation.
- Fuse (630mA) + Zener diode (62V) connected before step down 
    - In case of overvoltage the Zener breaks and causes sufficient amperage to burn the fuse.
    - Connected before step down convertor.
- Step down is set to 5V and powers all the electronics.

 
 



# Future 
**TBD / not finished**
- [x] - subtract voltages from each other to get net voltages staright from the logger
- [x] - debug switch to change behavior for development/troubleshooting  
  - different LCD and CLI printout

**Possible future features**
- [ ] - replace fuses with PTC/Polyfuse
  - suitable RC circuit would have to be designed due to slow polyfuse react times
- [ ] - use ALRT/RDY pin on ADS1115 to verify it's ready 
- [x] - automatic selection of the power line based on the max. voltage  
  - DONE, handled in analog