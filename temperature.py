#!/usr/bin/env python

"""

HiveOS-Monitor

HiveOS and currency monitoring script with temperature monitoring and heat management.

This script is always running and I monitor it constantly; the values output to the CLI are those that 
I find most useful. The temperature reading and SSH based OC adjusting worked well for my first (hot)
summer of mining. The OC adjusting parts are commented out and have not been tested for a while (autofan!)

Temperature system interacts with Adafruit IO to provide historical charts and graphs. Sensors are based on 
Adafruit Feather M0 900MHz packet radio boards (not LoRa). Written for a single farm/miner/currency so there 
will be bugs as it is expanded to larger Hive setups and different currencies. I would be happy to add more 
details on the temperature sensing / OC adjusting if there is interest.

I have added the Featheer M0 source files and referenced shell scripts to the sensenet directory in this
git repository. Let me know what I missed.

Project files:
    hiveos.py      - main script and stdout output code
    temperature.py - temperature monitor / SSH based OC control. Interacts with Adafruit IO for UI goodness
    webhelpers.py  - web data fetch and parsing methods
    secrets.py     - account login credentials

Greg Eigsti
greg@eigsti.com

"""

import re
import sys
import time

# project imports
import secrets

# read temp sensor data from hardware
import serial
import threading
# Import Adafruit IO REST client.
from Adafruit_IO import Client
import paramiko


########################################################################################################################
## temperature sensor and ssh oc changing stuff
########################################################################################################################

thread_run = True
#sensor_lock = threading.Lock()
gateway_temp_f = 0.0
miner_temp_f = 0.0
outside_temp_f = 0.0
miner_oc_high = True


########################################################################################################################
## start temperature sensor thread
########################################################################################################################
def start():
    global thread_run
    thread_run = True
    t = threading.Thread(target=sensorthread)
    t.start()

########################################################################################################################
## stop temperature sensor thread
## TODO: cannot get thread to exit cleanly
########################################################################################################################
def stop():
    thread_run = False
    time.sleep(1)

########################################################################################################################
## temperature sensor thread
########################################################################################################################
def sensorthread():
    global thread_run
    global gateway_temp_f
    global miner_temp_f
    global outside_temp_f

    aio = Client(secrets.ADAFRUIT_IO_KEY)
    port = serial.Serial("/dev/ttyACM0", baudrate=115200, timeout=3.0)

    while thread_run:
        rcv = port.readline()
        if len(rcv) > 0:
            report = rcv.strip()

            regex_gw = '(\d+:\d+:\d+),GW,T,(-?\d+\.\d+),H,(\d+\.\d+),P,(\d+\.\d+),A,(-?\d+\.\d+)'
            result = re.match(regex_gw, report)
            if result:
                timestamp = result.group(1)
                temperature = 9.0 / 5.0 * float(result.group(2)) + 32
                gateway_temp_f = temperature
                humidity = result.group(3)
                pressure = float(result.group(4)) * 0.00029530
                altitude = result.group(5)

                print 'GATEWAY', timestamp, temperature, humidity, float(pressure) * 100.0, altitude
                # print aio.feeds()

                try:
                    aio.send('sensenet.gateway-humidity', float(humidity))
                    aio.send('sensenet.gateway-pressure', float(pressure) * 100.0)
                    aio.send('sensenet.gateway-temperature', float(temperature))
                except:
                    print("Unexpected error GW:", sys.exc_info()[0])

            regex_rx = '(\d+:\d+:\d+),RX,(\d+),RSSI,(-?\d+),(\d+:\d+:\d+),V,(\d+\.\d+),(\d+),B,(\d+\.\d+),T,(-?\d+\.\d+),H,(\d+\.\d+)'
            result = re.match(regex_rx, report)
            if result:
                timestamp = result.group(1)
                from_addr = int(result.group(2))
                rssi = result.group(3)
                time_remote = result.group(4)
                version = result.group(5)
                packet_id = result.group(6)
                battery = result.group(7)
                temperature = 9.0 / 5.0 * float(result.group(8)) + 32
                humidity = result.group(9)

                print 'REMOTE ', timestamp, from_addr, rssi, time_remote, version, packet_id, battery, temperature, humidity

                try:
                    if from_addr == 2:
                        aio.send('sensenet.bathroom-battery', float(battery))
                        aio.send('sensenet.bathroom-humidity', float(humidity))
                        aio.send('sensenet.bathroom-temperature', float(temperature))
                        miner_temp_f = temperature
                    elif from_addr == 3:
                        aio.send('sensenet.outside-battery', float(battery))
                        aio.send('sensenet.outside-humidity', float(humidity))
                        aio.send('sensenet.outside-temperature', float(temperature))
                        outside_temp_f = temperature
                    else:
                        print '!!! WTF ??? !!!'
                except:
                    print("Unexpected error RX:", sys.exc_info()[0])

########################################################################################################################
## checks reported temperatures and sets miner OC profile. worked well all summer to under/over clock
## single miner in reesponse to miner room temperature. Has not been in use/tested since this major rewrite
########################################################################################################################
def check_temperatures():
    global miner_oc_high

    print 'OC:{} GW:{}F Miner:{}F Outside:{}F'.format(miner_oc_high, gateway_temp_f, miner_temp_f, outside_temp_f)

    # not tested for a while; since at least one major refactor.
    # should work or get you most of the way there, not tested reecently...
    """
    if miner_temp_f != 0.0:
        ssh_command = None
        if miner_temp_f >= 80.0 and miner_oc_high == True:
            print '!!! REDUCE NVIDIA OC !!!'
            miner_oc_high = False
            ssh_command = '/home/user/nvidia-oc-low'
        elif miner_temp_f <= 75.0 and miner_oc_high == False:
            print '!!! INCREASE NVIDIA OC !!!'
            miner_oc_high = True
            ssh_command = '/home/user/nvidia-oc-high'

        if ssh_command:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(secrets.MINER_IPADDR, username=secrets.MINER_USER, password=secreets.MINER_PASS)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(ssh_command, get_pty=True)

            for line in ssh_stdout:
                print line

            for line in ssh_stderr:
                print line

    print ''
    """


#####################################################################################
## main script entry point
#####################################################################################
if __name__ == '__main__':
    print('Intended to be exeuted as a HiveOS-Monitor library')
