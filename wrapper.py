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

last_rx = 0
last_tx = 0
last_time = 0
def get_net_speed():
    """ Get the current net speed. """
    import psutil, time
    global last_time, last_rx, last_tx
    tx, rx = psutil.net_io_counters()[:2]

    now = time.time()
    interval = now - last_time

    down = (rx - last_rx) / interval
    up = (tx - last_tx) / interval
    #sys.stderr.write("rx: {}, tx: {}, interval: {}, down: {}, up: {}\n".format(rx, tx, interval, down, up))
    if interval > 0: # safety measure
        rate="{}↓ {}↑".format(make_io_speed_readable(down), make_io_speed_readable(up))
    else:
        rate = ""

    # set the last_* variables
    last_rx = rx
    last_tx = tx
    last_time = now
    return rate

last_read_counter = 0
last_write_counter = 0
last_time_io = 0
def get_io_speed():
    """ Get the current write/read-rate on disks. """
    import psutil, time
    global last_time_io, last_read_counter, last_write_counter
    read, write = psutil.disk_io_counters()[2:4]

    now = time.time()
    interval = now - last_time_io

    read_rate = (read - last_read_counter) / interval
    write_rate = (write - last_write_counter) / interval
    sys.stderr.write("write: {}, read: {}, interval: {}, read_rate: {}, write_rate: {}\n".format(write, read, interval, read_rate, write_rate))

    if interval > 0: # safety measure
        rate="w:{} r:{}".format(make_io_speed_readable(write_rate),make_io_speed_readable(read_rate))
    else:
        rate = ""

    # set the last_* variables
    last_write_counter = write
    last_read_counter = read
    last_time_io = now
    return rate


def make_io_speed_readable(inp, input_unit='bytes'):
    if input_unit != 'bytes':
        raise NotImplemented
    lbytes = int(inp)
    kib = lbytes >> 10
    if kib < 0:
        return "? K"
    elif kib > 1024:
        return "{number:.{digits}f} M".format(number=(kib / 1024), digits=2)
    else:
        return "{} K".format(kib)

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
        keymap, keymap_color = get_keymap()
        j.insert(-1, {'full_text' : '{}'.format(keymap),
                     'color' : '{}'.format(keymap_color),
                     'name' : 'gov'})
        j.insert(0, {'full_text' : '{}'.format(get_net_speed()), 'name' : 'net_speed'})
        j.insert(0, {'full_text' : '{}'.format(get_io_speed()), 'name' : 'io'})
        # and echo back new encoded json
        print_line(prefix+json.dumps(j))
