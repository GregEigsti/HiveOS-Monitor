# HiveOS-Monitor
HiveOS and currency monitoring script with temperature monitoring and under/overclocks for heat management.

SenseNet integration

SenseNet in an Adafruit Feather M0 based temperature/etc. sensing network which includes remote and gateway
devices. HiveOS-Monitor interacts with miner temperature data and can under/overclock a miner (currently one)
to aid with heat management. Under/oveerclocking is achieved by calling a preconfigured shell script on the 
miner via SSH.


Feather M0 with 900MHz packet radio
https://www.adafruit.com/product/3176
M0 source shows what sensors were used; all Adafruit parts.
Visit https://learn.adafruit.com/ to learn more about any of the parts used in this project.

Gateway and remote M0 code mostly the same with a few key differences.


Shell scripts on miner

nvidia-oc-high - sets high/hot OC profile
nvidia-oc-low - sets low/cool OC profile
Copies backup of Hive nvidia OC profile to current OC profile and applies.
To create a new hot profile - set a hot OC profile and apply in hive, then copy your miner's nvidia-oc.conf to nvidia-oc.conf.high...  The high script will use this backed up OC profile to later set the miner.


Greg Eigsti
greg@eigsti.com

