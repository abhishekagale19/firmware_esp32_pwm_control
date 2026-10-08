"""Fade the onboard LED (GPIO2) forever."""
from pwm_control import PWMController

led = PWMController(pin=2, freq=1000)
try:
    while True:
        led.breathe(cycles=1, period_ms=2000)
except KeyboardInterrupt:
    led.deinit()
