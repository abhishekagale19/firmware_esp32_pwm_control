"""On-device tests for pwm_control. Run: mpremote run tests/test_pwm.py"""
from pwm_control import PWMController, pwm_start
import time

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
    print(("PASS  " if cond else "FAIL  ") + name)


def raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


# 1. Default pin (GPIO 2, onboard LED)
led = PWMController(2, 1000, 0)
check("create on GPIO2", led.pin == 2)

# 2. Frequency
for f in (100, 1000, 5000):
    led.set_frequency(f)
    check("frequency %d Hz" % f, led.get_frequency() == f)

# 3. Duty cycle
for d in (0, 25, 50, 75, 100):
    led.set_duty_percent(d)
    time.sleep_ms(300)
    check("duty %d%%" % d, abs(led.get_duty_percent() - d) < 1.0)

# 4. Invalid input is rejected
check("reject GPIO 6 (flash pin)", raises(lambda: PWMController(6)))
check("reject GPIO 34 (input only)", raises(lambda: PWMController(34)))
check("reject duty 150%", raises(lambda: led.set_duty_percent(150)))
check("reject freq 0", raises(lambda: led.set_frequency(0)))

# 5. Visual: fade + breathe on onboard LED
led.fade(0, 100, 1500)
led.fade(100, 0, 1500)
led.breathe(cycles=2, period_ms=2000)
check("fade/breathe ran", True)
led.deinit()

# 6. Multiple pins (probe with a scope/LED/logic analyser)
for p in (4, 5, 18, 19, 23):
    c = pwm_start(p, 2000, 50)
    time.sleep_ms(200)
    check("PWM on GPIO%d" % p, abs(c.get_duty_percent() - 50) < 1.0)
    c.deinit()

print("\nResult: %d passed, %d failed" % (passed, failed))
