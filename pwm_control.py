"""
pwm_control - PWM helper library for ESP32 (MicroPython)

Configure pin, frequency and duty cycle, and fade/breathe an LED.
Default pin is GPIO 2 (onboard LED on most ESP32 DevKit boards).
"""
from machine import Pin, PWM
import time

__version__ = "1.0.0"

# Output-capable GPIOs that are safe for PWM on a standard ESP32 DevKit.
# Excluded: 0 and 12 (boot strapping), 1/3 (UART0), 6-11 (SPI flash),
# 34-39 (input only).
VALID_PINS = (2, 4, 5, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)

MAX_DUTY_U16 = 65535


def _check_pin(pin):
    if pin not in VALID_PINS:
        raise ValueError("GPIO %s not usable for PWM. Valid: %s" % (pin, VALID_PINS))


def _check_freq(freq):
    if not isinstance(freq, int) or freq < 1 or freq > 40000000:
        raise ValueError("freq must be an int between 1 and 40000000 Hz")


def _check_percent(p):
    if p < 0 or p > 100:
        raise ValueError("duty percent must be between 0 and 100")


def _pct_to_u16(p):
    return int(p * MAX_DUTY_U16 / 100)


class PWMController:
    """PWM output on one GPIO pin."""

    def __init__(self, pin=2, freq=1000, duty_percent=0):
        _check_pin(pin)
        _check_freq(freq)
        _check_percent(duty_percent)
        self.pin = pin
        self._pwm = PWM(Pin(pin, Pin.OUT))
        self._pwm.freq(freq)
        self._pwm.duty_u16(_pct_to_u16(duty_percent))

    # --- configuration -------------------------------------------------
    def set_frequency(self, freq):
        _check_freq(freq)
        self._pwm.freq(freq)

    def get_frequency(self):
        return self._pwm.freq()

    def set_duty_percent(self, percent):
        _check_percent(percent)
        self._pwm.duty_u16(_pct_to_u16(percent))

    def set_duty_u16(self, duty):
        if duty < 0 or duty > MAX_DUTY_U16:
            raise ValueError("duty must be between 0 and 65535")
        self._pwm.duty_u16(duty)

    def get_duty_percent(self):
        return round(self._pwm.duty_u16() * 100 / MAX_DUTY_U16, 1)

    # --- effects -------------------------------------------------------
    def fade(self, start=0, end=100, duration_ms=1000, steps=100):
        """Linearly change duty from start% to end% over duration_ms."""
        _check_percent(start)
        _check_percent(end)
        delay = max(1, duration_ms // steps)
        for i in range(steps + 1):
            self.set_duty_percent(start + (end - start) * i / steps)
            time.sleep_ms(delay)

    def breathe(self, cycles=3, period_ms=2000, steps=100):
        """Fade up then down, repeated 'cycles' times."""
        half = period_ms // 2
        for _ in range(cycles):
            self.fade(0, 100, half, steps)
            self.fade(100, 0, half, steps)

    def off(self):
        self.set_duty_percent(0)

    def deinit(self):
        self._pwm.deinit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()


def pwm_start(pin=2, freq=1000, duty_percent=50):
    """Shortcut: create a controller and start PWM immediately."""
    return PWMController(pin, freq, duty_percent)
