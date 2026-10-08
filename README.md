Quick start (just want to try it?)

You don't need to build anything. The finished firmware is in the firmware/ folder.

1. Install the tools

bash
python3 -m venv ~/esp/venv
. ~/esp/venv/bin/activate
pip install esptool mpremote

2. Plug in your ESP32 and find its port

bash
ls /dev/ttyUSB* /dev/ttyACM*

If you get "permission denied" later, run sudo usermod -a -G dialout $USER and log out and back in.

3. Flash the firmware

bash
esptool --chip esp32 --port /dev/ttyUSB0 erase-flash
esptool --chip esp32 --port /dev/ttyUSB0 --baud 460800 write-flash -z 0x1000 firmware/esp32_pwm_firmware.bin

If flashing fails with "Failed to start stub flasher" (it happened to me), skip the stub and slow down:

bash
esptool --chip esp32 --port /dev/ttyUSB0 --no-stub erase-flash
esptool --chip esp32 --port /dev/ttyUSB0 --baud 115200 --no-stub write-flash 0x1000 firmware/esp32_pwm_firmware.bin

It takes a few minutes, but it works. Also try a different USB cable or port, and hold the BOOT button while it says "Connecting...".

4. Try it

bash
mpremote connect /dev/ttyUSB0 repl
python
from pwm_control import pwm_start

led = pwm_start(2, 1000, 50)   # GPIO 2, 1 kHz, 50% brightness
led.fade(0, 100, 1500)         # fade up over 1.5 seconds
led.breathe(cycles=3)          # breathing effect
led.deinit()

The blue LED on your board should change brightness. (Press Ctrl+] to leave the REPL.)

Using the library
python
from pwm_control import PWMController

led = PWMController(pin=2, freq=1000, duty_percent=0)

led.set_duty_percent(50)     # half brightness
led.set_frequency(5000)      # change the frequency
led.fade(0, 100, 2000)       # fade up over 2 seconds
led.breathe(cycles=3)        # up and down, three times
led.deinit()                 # release the pin when you're done

It also works as a context manager, so cleanup happens automatically:

python
with PWMController(2, 1000) as led:
    led.fade(0, 100, 1000)
API at a glance
Function	What it does
PWMController(pin=2, freq=1000, duty_percent=0)	Starts PWM on a GPIO. Raises ValueError for a bad pin, frequency or duty.
set_frequency(hz) / get_frequency()	Set or read the frequency (1 Hz to 40 MHz).
set_duty_percent(p) / get_duty_percent()	Set or read the duty cycle, 0 to 100 %.
set_duty_u16(d)	Set the raw 16-bit duty, 0 to 65535.
fade(start, end, duration_ms, steps)	Smoothly change brightness between two values.
breathe(cycles, period_ms)	Fade up and down, repeated.
off() / deinit()	Set duty to 0 / free the PWM channel.
pwm_start(pin, freq, duty_percent)	One-liner helper that creates and starts PWM.
Pins you can use

2, 4, 5, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33

These are deliberately left out: GPIO 0 and 12 (boot strapping), 1 and 3 (UART), 6 to 11 (connected to the flash chip) and 34 to 39 (input only).

Running the tests

With the board connected and the custom firmware flashed:

bash
mpremote connect /dev/ttyUSB0 run tests/test_pwm.py

The script checks pin creation, frequency, duty cycle, bad-input handling, a visible fade on the onboard LED, and PWM on GPIO 4, 5, 18, 19 and 23. Each line says PASS or FAIL, with a summary at the end.

The tests confirm the library behaves correctly. To actually see the signal on the extra pins, hook up an LED (with a resistor), a scope or a logic analyser.

You can also run the breathing-LED demo:

bash
mpremote connect /dev/ttyUSB0 run examples/pwm_led_fade.py
Building the firmware yourself (Ubuntu)

Want to rebuild the .bin from scratch? This is exactly what I did. It was tested with MicroPython v1.24.1 and ESP-IDF v5.2.2.

Each MicroPython release expects a specific ESP-IDF version. If you use a different MicroPython tag, check ports/esp32/README.md for the matching IDF version.

1. Install dependencies

bash
sudo apt update
sudo apt install -y git wget flex bison gperf python3 python3-pip python3-venv \
    cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 build-essential
sudo usermod -a -G dialout $USER     # then log out and back in

2. Install ESP-IDF

bash
mkdir -p ~/esp && cd ~/esp
git clone -b v5.2.2 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32
. ./export.sh          # run this in every new terminal before building

Check it worked: idf.py --version should print ESP-IDF v5.2.2.

3. Get MicroPython

bash
cd ~/esp
git clone https://github.com/micropython/micropython.git
cd micropython
git checkout v1.24.1
git submodule update --init --recursive
make -C mpy-cross

4. Add the library to the firmware

Anything in ports/esp32/modules/ gets frozen into the firmware automatically:

bash
cp /path/to/this/repo/src/pwm_control.py ~/esp/micropython/ports/esp32/modules/

5. Build

bash
. ~/esp/esp-idf/export.sh
cd ~/esp/micropython/ports/esp32
make submodules
make BOARD=ESP32_GENERIC clean
make BOARD=ESP32_GENERIC -j$(nproc)

The first build takes a while (5 to 15 minutes on my laptop). When it's done you'll find:

build-ESP32_GENERIC/firmware.bin      # combined image: bootloader + partition table + app

6. Flash it

Same as the quick start, using your freshly built file. The flash offset is 0x1000 for the original ESP32.

Troubleshooting
Problem	What to try
Permission denied on /dev/ttyUSB0	Add yourself to the dialout group, then log out and back in.
Board not detected	Use a data USB cable (not charge-only) and plug straight into the laptop, not a hub.
Failed to start stub flasher	Use --no-stub and --baud 115200, as shown above.
Stuck on Connecting......	Hold the BOOT button when the command starts, release once it connects.
ImportError: no module named pwm_control	The file wasn't in ports/esp32/modules/ at build time. Copy it there, run make clean, rebuild.
Build complains about the IDF version	Use the IDF version listed in ports/esp32/README.md for your MicroPython tag.
LED looks inverted	Some boards wire the LED active-low. Use 100 - value, or put an external LED on another pin.
Tested on
ESP32-D0WD-V3 (revision v3.1) dev board, onboard LED on GPIO 2
Ubuntu with MicroPython v1.24.1, ESP-IDF v5.2.2 and esptool v5.4.0
