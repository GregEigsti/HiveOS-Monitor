# HiveOS-Monitor
HiveOS and currency monitoring script with temperature monitoring and heat management.

  * Displays relevant data via CLI/stdout interface
  * Monitors HiveOS farms/miners
  * Monitors miner temperature
  * Gathers crypto currency data real time
  * Under/overclock miner based on temperature

Temperature system interacts with Adafruit IO to provide historical charts and graphs. Sensors are based on 
Adafruit Feather M0 900MHz packet radio boards (not LoRa).

Project files:
    hiveos.py      - main script and stdout output code
    temperature.py - temperature monitor / SSH based OC control. Interacts with Adafruit IO for UI goodness
    webhelpers.py  - web data fetch and parsing methods
    secrets.py     - account login credentials

Attribution is nice; if you make a pile of money with this code throw me a few duckets or offer me a job ;)

Greg Eigsti
greg@eigsti.com
