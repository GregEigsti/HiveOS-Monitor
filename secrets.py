#!/usr/bin/env python

"""

HiveOS-Monitor

HiveOS and currency monitoring script with temperature monitoring and under/overclocks for heat management.

This project is a system to 
  * monitor HiveOS collateral
  * gather related crypto currency data real time
  * monitor miner temperature
  * under/overclock miner based on temperature
  * display relevant data via CLI/stdout interface

This script is always running and I monitor it constantly; the values output to the CLI are those that 
I find most useful. The temperature reading and SSH based OC adjusting worked well for my first (hot)
summer of mining. The OC adjusting parts are commented out and have not been tested for a while (autofan!)

Temperature system interacts with Adafruit IO to provide historical charts and graphs. Sensors are based on 
Adafruit Feather M0 900MHz packet radio boards (not LoRa). Written for a single farm/miner/currency so there 
will be bugs as it is expanded to larger Hive setups and different currencies. I would be happy to add more 
details on the temperature sensing / OC adjusting if theere is interest.

Use of these scripts are at your own risk and ou will need to add your account secrets to secrets.py

Project files:
    hiveos.py      - main script and stdout output code
    temperature.py - temperature monitoring and SSH based OC control. Also interacts with Adafruit IO for UI goodness
    webhelpers.py  - web data fetch and parsing methods
    secrets.py     - account login credentials

If I had to pick a license it would be MIT. Attribution is nice; if you make a pile of money with my code throw me
a few duckets or offer me a job ;)

Greg Eigsti
greg@eigsti.com

"""

########################################################################################################################
## keys and secrets
########################################################################################################################
# Hive account
HIVE_USER = 'replace'
HIVE_PASS = 'replace'

# Adafruit IO
ADAFRUIT_IO_KEY = 'replace'

# Miner SSH account for OC updates
MINER_USER = 'replace'
MINER_PASS = 'replace'
MINER_IPADDR = '192.168.0.10'


#####################################################################################
## main script entry point
#####################################################################################
if __name__ == "__main__":
    print 'Intended to be run as a library'

