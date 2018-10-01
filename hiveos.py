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

import datetime
import os
import sys
import time

# project imports
import temperature as temp
import webhelpers as wh


########################################################################################################################
## prints a row seen in the per miner grid in stdout. TEMPC, HASH, etc.
########################################################################################################################
def printrow(label, data, crlf=True, flt=False):
    print label,
    try:
        for item in data:            
            #TODO: total cheeseball, just to get it working
            if flt and int(item) < 10000:
                print '{:5d}'.format(int(float(item) * 1000)),
            else:
                print '{:5d}'.format(int(item)),

    except ValueError:
        print data

    if crlf:
        print

#####################################################################################3
## McGucket GPU info
#####################################################################################3
"""
GPU0, PCI1, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:01:00.0, Device 196e:1211 - PNY
GPU1, PCI2, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:02:00.0, ZOTAC International (MCO) Ltd. Device 1474 - shorty
GPU2, PCI3, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:03:00.0, eVga.com. Corp. Device 6696 - over MB
GPU3, PCI4, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:04:00.0, eVga.com. Corp. Device 6696 - over PS
GPU4, PCI5, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:05:00.0, Gigabyte Technology Co., Ltd Device 376b - over MB
GPU5, PCI6, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:06:00.0, ZOTAC International (MCO) Ltd. Device 2471 AMP
GPU6, PCI8, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:08:00.0, Micro-Star International Co., Ltd. [MSI] Device 3603
GPU7, PCI9, GeForce GTX 1080 Ti, 11172 MB PCI: 0000:09:00.0, Gigabyte Technology Co., Ltd Device 376b - over PS
"""

def main():
    #####################################################################################
    ## Start sensor read thread. 
    #####################################################################################
    temp.start()

    #####################################################################################
    ## Loop, sleep 30, rinse, repeat
    #####################################################################################
    while True:
        try:
            wallets = []
            account = None
            zcash_price = None
            zcash_diff = None
            eth_price = None
            eth_diff = None

            #####################################################################################
            ## Login to hive, if needed, and get farm(s) data
            #####################################################################################
            wh.hive_login()
            farms = wh.get_farms()

            #####################################################################################
            ## Iterate through hive farms and
            ##  get and cache hive wallets
            ##  Iterate through farm workers
            ##   pick out and print hive farm data
            #####################################################################################
            for farm in farms:
                farm_wallets = wh.get_farm_wallets(farm)
                for worker in wh.get_farm_workers(farm):
                    print '----------------------------------------------------------------------'
                    print str(datetime.datetime.today())

                    total_khs = float(worker['miners_summary']['hashrates'][0]['hash'])
                    print worker['name'], \
                          worker['ip_addresses'][0], \
                          worker['miners_summary']['hashrates'][0]['miner'], \
                          worker['miners_summary']['hashrates'][0]['algo'], \
                          '{:1.3f}'.format(total_khs)

                    #print 'acc: {}, inv {}, rej {}, ratio {}'.format(
                    #    worker['miners_summary']['hashrates'][0]['shares']['accepted'],
                    #    worker['miners_summary']['hashrates'][0]['shares']['invalid'],
                    #    worker['miners_summary']['hashrates'][0]['shares']['rejected'],
                    #worker['miners_summary']['hashrates'][0]['shares']['ratio'])
                    print 'acc: {}, inv {}, rej {}'.format(
                        worker['miners_summary']['hashrates'][0]['shares']['accepted'],
                        worker['miners_summary']['hashrates'][0]['shares']['invalid'],
                        worker['miners_summary']['hashrates'][0]['shares']['rejected'])

                    #oc change ability commented out. only displays current temps.
                    temp.check_temperatures()

                    oc = wh.get_worker_oc(farm, worker)

                    power_list = []
                    for gpu in worker['gpu_stats']:
                        power_list.append(gpu['power'])

                    print '        GPU0 GPU1 GPU2 GPU3 GPU4 GPU5 GPU6 GPU7'
                    print '      ------------------------------------------------'
                    printrow('TEMPC |', worker['miners_stats']['hashrates'][0]['temps'])
                    printrow('HASH  |', worker['miners_stats']['hashrates'][0]['hashes'], crlf=False, flt=True)
                    print ' {:1.3f}'.format(total_khs)
                    printrow('CLOCK |', oc['oc_config']['default']['nvidia']['core_clock'].split())
                    printrow('POWER |', power_list, crlf=False)
                    print ' {:d}'.format(int(worker['stats']['power_draw']))
                    printrow('PWRLIM|', oc['oc_config']['default']['nvidia']['power_limit'].split())
                    printrow('MEM   |', oc['oc_config']['default']['nvidia']['mem_clock'].split())
                    #printrow('NVFAN |', oc['oc_config']['default']['nvidia']['nvidia_fan'].split())
                    printrow('FAN   |', oc['oc_config']['default']['nvidia']['fan_speed'].split())

                #####################################################################################
                ## Iterate through cached wallets for this farm
                ##  get and cache wallet info, cash price, difficulty
                #####################################################################################
                for wallet in farm_wallets:
                    unconfirmed = 0.0
                    unpaid = 0.0
                    balance = 0.0
                    price = 0.0
                    difficulty = 0.0
                    price_data = None
                    diff_data = None

                    wal = wallet['wal']
               
                    #####################################################################################
                    ## Fetch and store ZEC wallet info, price, difficulty
                    #####################################################################################
                    if wallet['coin'] == 'ZEC':
                        price = wh.get_zcash_price()
                        difficulty = wh.get_zcash_difficulty()
                        balance = wh.get_zcash_balance(wal)

                        account = wh.get_zcash_account(wal)
                        if account and account['data'] != 'NO DATA':
                            if account['data']['unconfirmed']:
                                unconfirmed = float(account['data']['unconfirmed']) / 1000000.0
                            if account['data']['unpaid']:
                                unpaid = float(account['data']['unpaid']) / 1000000.0

                        wallets.append({'coin': wallet['coin'],
                                'price': price,
                                'difficulty': difficulty,
                                'name': wallet['name'],
                                'unconfirmed': unconfirmed,
                                'unpaid': unpaid,
                                'wal': wal,
                                'balance': balance})

                    #####################################################################################
                    ## Fetch and store ETH wallet info, price, difficulty
                    #####################################################################################
                    elif wallet['coin'] == 'ETH':
                        price = wh.get_eth_price()
                        difficulty = wh.get_eth_difficulty()
                        balance = wh.get_eth_balance(wal)

                        account = wh.get_eth_account(wal)
                        if account:
                            unpaid = account['data']['currentStatistics']['unpaid'] / 1000000000000000000.0
                            staleShares = account['data']['currentStatistics']['staleShares']
                            activeWorkers = account['data']['currentStatistics']['activeWorkers']
                            invalidShares = account['data']['currentStatistics']['invalidShares']
                            validShares = account['data']['currentStatistics']['validShares']

                            wallets.append({'coin': wallet['coin'], 
                                'price': price,
                                'difficulty': difficulty,
                                'name': wallet['name'], 
                                'unconfirmed': unconfirmed, 
                                'unpaid': unpaid, 'wal': wal, 
                                'balance': balance, 
                                'staleShares': staleShares, 
                                'activeWorkers': activeWorkers, 
                                'invalidShares': invalidShares, 
                                'validShares': validShares})

                    #####################################################################################
                    ## Fetch and store XVG wallet info, price, difficulty
                    #####################################################################################
                    elif wallet['coin'] == 'XVG':
                        price = wh.get_verge_price()
                        difficulty = wh.get_verge_difficulty()

                        account = wh.get_verge_account(wal)
                        if account:
                            #print account
                            unconfirmed = account['unsold']
                            balance = account['total'] - account['unpaid']

                            wallets.append({'coin': wallet['coin'], 
                                'price': price,
                                'difficulty': difficulty,
                                'name': wallet['name'], 
                                'unconfirmed': unconfirmed, 
                                'unpaid': account['balance'], 
                                'wal': wal, 
                                'balance': balance})

                    #####################################################################################
                    ## Fetch and store XMR wallet info, price, difficulty
                    #####################################################################################
                    elif wallet['coin'] == 'XMR':
                        price = wh.get_monero_price()
                        difficulty = wh.get_monero_difficulty()

                        #TODO: add monero wallet info

                        wallets.append({'coin': wallet['coin'], 
                            'price': price,
                            'difficulty': difficulty,
                            'name': wallet['name'], 
                            'unconfirmed': unconfirmed, 
                            'unpaid': unpaid, 
                            'wal': wal, 
                            'balance': balance})

                    else:
                        wallets.append({'coin': wallet['coin'], 
                            'price': 'TBI',
                            'difficulty': 'TBI',
                            'name': wallet['name'], 
                            'unconfirmed': 'TBI', 
                            'unpaid': 'TBI', 
                            'wal': wal, 
                            'balance': 'TBI'})

            print '======================================================================'

            print 'Workers on: {} GPUs on: {} Workers off: {} GPUs off: {}'.format(
                farms[0]['stats']['workers_online'],
                farms[0]['stats']['gpus_online'],
                farms[0]['stats']['workers_offline'],
                farms[0]['stats']['gpus_offline'])

            #####################################################################################
            ## Iterate through all cached wallets and display 
            ##  cash price / difficulty and wallet info
            #####################################################################################
            for wallet in wallets:
                #####################################################################################
                ## Display ZEC wallet info, price, difficulty
                #####################################################################################
                if wallet['coin'] == 'ZEC':
                    print '{}: \'{}\' {}\n Unc: {} Unp: {}, Tot: {}, Bal: {} (${:1.2f})'.format(
                        wallet['coin'],
                        wallet['name'],
                        wallet['wal'],
                        wallet['unconfirmed'], wallet['unpaid'],
                        wallet['unconfirmed'] + wallet['unpaid'],
                        wallet['balance'], wallet['balance'] * wallet['price'])
                #####################################################################################
                ## Display ETH wallet info, price, difficulty
                #####################################################################################
                elif wallet['coin'] == 'ETH':
                    print '{}: \'{}\' {}\n Workers: {}, Stale: {}, Inv: {}, Val: {}, Unp: {} (${:1.2f}), Bal: {} (${:1.2f})'.format(
                        wallet['coin'],
                        wallet['name'],
                        wallet['wal'],
                        wallet['activeWorkers'],
                        wallet['staleShares'],
                        wallet['invalidShares'],
                        wallet['validShares'],
                        wallet['unpaid'],
                        wallet['unpaid'] * wallet['price'],
                        wallet['balance'], 
                        wallet['balance'] * wallet['price'])
                #####################################################################################
                ## Display XVG wallet info, price, difficulty
                #####################################################################################
                elif wallet['coin'] == 'XVG':
                    print '{}: \'{}\' {}\n Unc: {} Unp: {}, Tot: {} (${:1.2f}), Bal: {} (${:1.2f})'.format(
                        wallet['coin'],
                        wallet['name'],
                        wallet['wal'],
                        wallet['unconfirmed'], 
                        wallet['unpaid'],
                        wallet['unconfirmed'] + wallet['unpaid'],
                        (wallet['unconfirmed'] + wallet['unpaid']) * wallet['price'],
                        wallet['balance'], 
                        wallet['balance'] * wallet['price'])
                #####################################################################################
                ## Display XMR wallet info, price, difficulty
                #####################################################################################
                elif wallet['coin'] == 'XMR':
                    print '{}: \'{}\' {}\n Unc: {} Unp: {}, Tot: {} (${:1.2f}), Bal: {} (${:1.2f})'.format(
                        wallet['coin'],
                        wallet['name'],
                        wallet['wal'],
                        wallet['unconfirmed'], 
                        wallet['unpaid'],
                        wallet['unconfirmed'] + wallet['unpaid'],
                        (wallet['unconfirmed'] + wallet['unpaid']) * wallet['price'],
                        wallet['balance'], 
                        wallet['balance'] * wallet['price'])
                #####################################################################################
                ## New wallet added to Hive?
                #####################################################################################
                else:
                     print 'New coin: {}'.format(wallet['coin'])

                print ' Price: ${:1.2f} Difficulty: {}'.format(wallet['price'], wallet['difficulty'])

            print '======================================================================'

        except KeyboardInterrupt:
            print 'KeyboardInterrupt'
            if temp:
                temp.stop()
            sys.exit()
        except Exception as e:
            print 'ERROR: unhandled: {}'.format(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        time.sleep(30)


#####################################################################################
## main script entry point
#####################################################################################
if __name__ == "__main__":
    main()

