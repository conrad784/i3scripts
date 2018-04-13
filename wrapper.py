#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# To use it, ensure your ~/.i3status.conf contains this line:
#     output_format = "i3bar"
# in the 'general' section.
# Then, in your ~/.i3/config, use:
#     status_command i3status | <path_to_script>/wrapper.py
# In the 'bar' section.
#

import sys
import json

### define some default colors
color_ok = "#FFFFFF" # white
color_good = "#009E00" # green
color_degraded = "#FFA500" # orange
color_bad = "#CC1616" # red

### getting data from various locations
def get_governor():
    """ Get the current governor for cpu0, assuming all CPUs use the same. """
    with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor') as fp:
        return fp.readlines()[0].strip()

def get_keymap():
    """ Get the currently used keymap. """
    import subprocess
    cmd = ["setxkbmap", "-query"]
    out = subprocess.check_output(cmd).decode()
    o = out.split()
    odict = {o[i][:-1]: o[i+1] for i in range(0, len(o), 2)}
    lg = odict.get("variant") or odict.get("layout")
    if lg == "de":
        color = color_ok
    else:
        color = color_degraded
    return lg, color

last_rx = {}
last_tx = {}
last_time = 0
def get_net_speed(aggregated=False, ignore_iface=["lo", "virbr0", "virbr0-nic"]):
    """ Get the current net speed. """
    import psutil, time
    global last_time, last_rx, last_tx

    traffic = psutil.net_io_counters(pernic=True)
    now = time.time()
    interval = now - last_time
    rate_max = {"iface": None, "down": 0, "up": 0}
    rate_aggregated = {"iface": "C", "down": 0, "up": 0}
    for iface, counters in traffic.items():
        if iface in ignore_iface:
            continue
        tx, rx = counters[:2]

        down = (rx - last_rx.get(iface, rx)) / interval
        up = (tx - last_tx.get(iface, tx)) / interval
        #sys.stderr.write("\niface: {}, rx: {}, tx: {}, interval: {}, down: {}, up: {}\n".format(iface, rx, tx, interval, down, up))

        # set the last_* variables
        last_rx[iface] = rx
        last_tx[iface] = tx
        last_time = now

        rate_aggregated["down"] += down
        rate_aggregated["up"] += up
        if down+up > rate_max["down"]+rate_max["up"]:
            rate_max.update({"iface": iface, "down": down, "up": up})

    if aggregated:
        rate_max = rate_aggregated
    rate="{[0]}:{}↓ {}↑".format(str(rate_max["iface"]).capitalize(),
                                make_human_readable(rate_max["down"], '', True),
                                make_human_readable(rate_max["up"], '', True))
    return rate

last_read_counter = 0
last_write_counter = 0
last_time_io = 0
consecutive_io = 0
def get_io_speed():
    """ Get the current write/read-rate on disks. """
    import psutil, time
    global last_time_io, last_read_counter, last_write_counter, consecutive_io
    read, write = psutil.disk_io_counters()[2:4]

    now = time.time()
    interval = now - last_time_io

    read_rate = (read - last_read_counter) / interval
    write_rate = (write - last_write_counter) / interval
    #sys.stderr.write("\nwrite: {}, read: {}, interval: {}, read_rate: {}, write_rate: {}\n".format(write, read, interval, read_rate, write_rate))

    if read_rate or write_rate:
        consecutive_io += 1
    r_write = Rate(('△','▲'))
    r_read =  Rate(('▽','▼'))
    if interval > 0 and consecutive_io > 2: # safety measure
        rate="{} {}".format(r_write(write_rate), r_read(read_rate))
        consecutive_io -= 1
    else:
        rate = "{} {}".format(r_write(0), r_read(0))

    # set the last_* variables
    last_write_counter = write
    last_read_counter = read
    last_time_io = now
    return rate

def get_disk_free(partition = "/"):
    import psutil
    return make_human_readable(psutil.disk_usage(partition)[2], decimals=1)

####### output formatting functions #######
class Rate(object):
    """"
    parameter 'indicators' evaluates takes first as empty and  last as filled indicator
    working examples: Rate(indicators = ('▽','▼')) or Rate(indicators = ('↑'))
    """
    def __init__(self, indicators):
        self.indicators = indicators

    def __call__(self, val, input_unit='bytes'):
        self.val = val
        return "{}:{}".format(self.indicator, make_human_readable(val, '', True))

    @property
    def indicator(self):
        if self.val:
            return self.indicators[-1]
        else:
            return self.indicators[0]


def make_human_readable(num, suffix='B', suppress_low=False, decimals=2):
    if suppress_low and abs(num) < 1024:
        return "{} K".format(int(num) >> 10)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{number:.{digits}f} {unit}{suffix}".format(number=num, digits=decimals, unit=unit, suffix=suffix)
        num /= 1024.0
    return "{number:.1f}{unit}{suffix}".format(number=num, unit='Yi', suffix=suffix)

########  output functions ########
def print_line(message):
    """ Non-buffered printing to stdout. """
    sys.stdout.write(message + '\n')
    sys.stdout.flush()

def read_line():
    """ Interrupted respecting reader for stdin. """
    # try reading a line, removing any extra whitespace
    try:
        line = sys.stdin.readline().strip()
        # i3status sends EOF, or an empty line
        if not line:
            sys.exit(3)
        return line
    # exit on ctrl-c
    except KeyboardInterrupt:
        sys.exit()

######## main starting ########
if __name__ == '__main__':
    # Skip the first line which contains the version header.
    print_line(read_line())

    # The second line contains the start of the infinite array.
    print_line(read_line())

    while True:
        line, prefix = read_line(), ''
        # ignore comma at start of lines
        if line.startswith(','):
            line, prefix = line[1:], ','
        j = json.loads(line)
        # insert information into the start of the json, but could be anywhere
        # CHANGE THIS LINE TO INSERT SOMETHING ELSE
        #j.insert(0, {'full_text' : '{}'.format(get_governor()), 'name' : 'gov'})

        # append to the right
        keymap, keymap_color = get_keymap()
        j.insert(-1, {'full_text' : '{}'.format(keymap),
                     'color' : '{}'.format(keymap_color),
                     'name' : 'gov'})

        # append to the left
        j.insert(0, {'full_text' : '{} ⛁{}'.format(get_io_speed(), get_disk_free()), 'name' : 'disk'})
        j.insert(0, {'full_text' : '{}'.format(get_net_speed()), 'name' : 'net_speed'})
        # and echo back new encoded json
        #sys.stderr.write("\n[DEBUG] full_j: {}\n\n".format(j))
        print_line(prefix+json.dumps(j))
