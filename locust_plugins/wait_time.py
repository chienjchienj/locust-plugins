import logging
import time
from locust.env import Environment
from locust import events, runners
from typing import Optional
from locust.wait_time import constant_pacing

runner: Optional[runners.LocustRunner] = None
_last_run = 0.0
_warning_emitted = False
_target_missed = False


@events.init.add_listener
def init(environment: Environment, **_kw):
    global runner
    runner = environment.runner  # type: ignore


@events.quitting.add_listener
def quitting(**_kw):
    if _warning_emitted:
        print(
            "Failed to reach targeted number of iterations per second (at some point during the test). Probably caused by target system overload or too few clients"
        )


def constant_ips(ips):
    return constant_pacing(1.0 / ips)


def constant_total_ips(ips: float):
    def func(_locust):
        global _warning_emitted, _target_missed, _last_run, runner
        if runner is None or runner.target_user_count is None:
            return 1 / ips
        current_time = time.time()
        delay = runner.target_user_count / ips
        next_time = _last_run + delay
        if current_time > next_time:
            if runner.state == runners.STATE_RUNNING and _target_missed and not _warning_emitted:
                logging.warning("Failed to reach target ips, even after rampup has finished")
                _warning_emitted = True  # stop logging
            _target_missed = True
            _last_run = current_time
            return 0
        _target_missed = False
        _last_run = next_time
        return delay

    return func
