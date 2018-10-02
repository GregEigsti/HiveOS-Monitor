#!/usr/bin/env python

"""

HiveOS-Monitor

HiveOS and currency monitoring script with temperature monitoring and heat management.

Project files:
    hiveos.py      - main script and stdout output code
    temperature.py - temperature monitor / SSH based OC control. Interacts with Adafruit IO for UI goodness
    webhelpers.py  - web data fetch and parsing methods
    secrets.py     - account login credentials

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
    print 'Intended to be exeuted as a HiveOS-Monitor library'
