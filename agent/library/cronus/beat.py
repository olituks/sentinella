"""
Implements the beat library

Author: Anay
Date created: 19th May 2014
"""

import datetime
import time

loop_start_time = None
loop_duration = 0

def get_total_seconds(td): 
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

def set_rate(rate):
    """Defines the ideal rate at which computation is to be performed

    :arg rate: the frequency in Hertz 
    :type rate: int or float

    :raises: TypeError: if argument 'rate' is not int or float
    """
    if not (isinstance(rate, int) or isinstance(rate, float)):
        raise TypeError("argument to set_rate is expected to be int or float")
    global loop_duration
    loop_duration = 1.0/rate

def sleep():
    """Sleeps for a dynamic duration of time as determined by set_rate() and true().
    
    :raises: BeatError: if this function is called before calling set_rate() or \
            before calling true()
    """
    if loop_duration == 0:
        raise BeatError("call beat.set_rate() before calling sleep")
    if loop_start_time == None:
        raise BeatError("call beat.true() before calling sleep")
    td = datetime.datetime.now() - loop_start_time
    duration_to_sleep = loop_duration - get_total_seconds(td)
    if duration_to_sleep < 0:
        raise BeatError("skipping sleep. Too much work!")
    time.sleep(duration_to_sleep)

def true():
    """A substitute to True. Use 'while beat.true()' instead of 'while True'
    
    :returns: True
    """
    global loop_start_time
    loop_start_time = datetime.datetime.now()
    return True


class BeatError:

    def __init__(self, msg):
        self.msg = msg
        pass

    def __str__(self):
        return self.msg
