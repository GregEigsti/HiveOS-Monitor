#!/usr/bin/env python

"""

HiveOS-Monitor

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

"""

import datetime
import os
import sys
import time

run_temperature = False
sleep_seconds = 30

# project imports
import webhelpers as wh
if run_temperature:
    import temperature as temp


########################################################################################################################
## prints a row seen in the per miner grid in stdout. TEMPC, HASH, etc.
########################################################################################################################
def printrow(label, data, crlf=True, flt=False):
    print(label),
    try:
        for item in data:            
            #TODO: total cheeseball, just to get it working
            if flt and int(item) < 10000:
                print('{:5d}'.format(int(float(item) * 1000))),
            else:
                print('{:5d}'.format(int(item))),

    except ValueError:
        print(data)

    if crlf:
        print('')

#####################################################################################
## Iterate through hive farms and workers pick out and print inteeresting data
#####################################################################################
def process_farm_workers(farm):

    if not farm:
        return

    for worker in wh.get_farm_workers(farm):
        #####################################################################################
        ## print header to stdout
        #####################################################################################
        print('----------------------------------------------------------------------')
        print(str(datetime.datetime.today()))
        print('\n{}'.format(worker['name'])),

        for item in worker['ip_addresses']:
            print(item),
        print('')

        for item in worker['miners_summary']['hashrates']:
            total_khs = float(item['hash'])
            print('{} {} {:1.3f}\nacc: {}, inv {}, rej {}, ratio {}'.format(
                 item['miner'],
                 item['algo'],
                 total_khs,
                 item['shares']['accepted'],
                 item['shares']['invalid'],
                 item['shares']['rejected'],
                 item['shares']['ratio']))

        # oc change ability commented out. only displays current temps.
        if run_temperature:
            temp.check_temperatures()

        # get hiveos reported oc data
        oc = wh.get_worker_oc(farm, worker)

        # get hiveos reported power use list
        power_list = []
        for gpu in worker['gpu_stats']:
            power_list.append(gpu['power'])

        #####################################################################################
        # print miner info table
        #####################################################################################
        print('\n        GPU0 GPU1 GPU2 GPU3 GPU4 GPU5 GPU6 GPU7')
        print('      ------------------------------------------------')
        # print hiveos miner temps
        for item in worker['miners_stats']['hashrates']:
            printrow('TEMPC |', item['temps'])
        # print hiveos miner hashes
        for item in worker['miners_stats']['hashrates']:
            printrow('HASH  |', item['hashes'], crlf=False, flt=True)
        #TODO: total_khs set above, could be invalid in multi-miner case?
        print(' {:1.3f}'.format(total_khs))
        printrow('CLOCK |', oc['oc_config']['default']['nvidia']['core_clock'].split())
        printrow('POWER |', power_list, crlf=False)
        print(' {:d}'.format(int(worker['stats']['power_draw'])))
        printrow('PWRLIM|', oc['oc_config']['default']['nvidia']['power_limit'].split())
        printrow('MEM   |', oc['oc_config']['default']['nvidia']['mem_clock'].split())
        # printrow('NVFAN |', oc['oc_config']['default']['nvidia']['nvidia_fan'].split())
        printrow('FAN   |', oc['oc_config']['default']['nvidia']['fan_speed'].split())

        print('Workers on: {} GPUs on: {} Workers off: {} GPUs off: {}\n'.format(
            farm['stats']['workers_online'],
            farm['stats']['gpus_online'],
            farm['stats']['workers_offline'],
            farm['stats']['gpus_offline']))

#####################################################################################
## Iterate through wallets for this farm
##  get and print wallet info, cash price, difficulty
#####################################################################################
def process_farm_wallets(farm_wallets):

    if not farm_wallets:
        return

    for wallet in farm_wallets:
        unconfirmed = 0.0
        unpaid = 0.0
        balance = 0.0
        price = 0.0
        difficulty = 0.0
        staleShares = 0.0
        activeWorkers = 0.0
        invalidShares = 0.0
        validShares = 0.0

        coin = wallet['coin']
        name = wallet['name']
        wal = wallet['wal']

        print('----------------------------------------------------------------------')

        #####################################################################################
        ## Fetch and store ZEC wallet info, price, difficulty
        #####################################################################################
        if coin == 'ZEC':
            price = wh.get_zcash_price()
            difficulty = wh.get_zcash_difficulty()
            balance = wh.get_zcash_balance(wal)
            account = wh.get_zcash_account(wal)
            if account and account['data'] != 'NO DATA':
                if account['data']['unconfirmed']:
                    unconfirmed = float(account['data']['unconfirmed']) / 1000000.0
                if account['data']['unpaid']:
                    unpaid = float(account['data']['unpaid']) / 1000000.0

        #####################################################################################
        ## Fetch and store ETH wallet info, price, difficulty
        #####################################################################################
        elif coin == 'ETH':
            price = wh.get_eth_price()
            difficulty = wh.get_eth_difficulty()
            balance = wh.get_eth_balance(wal)
            account = wh.get_eth_account(wal)
            if account:
                unpaid = account['data']['currentStatistics']['unpaid'] / 100000000000000000.0
                staleShares = account['data']['currentStatistics']['staleShares']
                activeWorkers = account['data']['currentStatistics']['activeWorkers']
                invalidShares = account['data']['currentStatistics']['invalidShares']
                validShares = account['data']['currentStatistics']['validShares']

        #####################################################################################
        ## Fetch and store XVG wallet info, price, difficulty
        #####################################################################################
        elif coin == 'XVG':
            price = wh.get_verge_price()
            difficulty = wh.get_verge_difficulty()
            balance = wh.get_verge_balance(wal)
            account = wh.get_verge_account(wal)
            if account:
                unconfirmed = account['unsold']
                unpaid = account['balance']

        #####################################################################################
        ## Fetch and store XMR wallet info, price, difficulty
        #####################################################################################
        elif coin == 'XMR':
            price = wh.get_monero_price()
            difficulty = wh.get_monero_difficulty()
            #TODO: add monero wallet info

        #####################################################################################
        ## Unknown coin
        #####################################################################################
        else:
            print('Unknown coin: {}'.format(coin))

        #####################################################################################
        ## Display wallet info, price, difficulty
        #####################################################################################
        if coin == 'ETH':
            print('{}: \'{}\' {}\n Workers: {}, Stale: {}, Inv: {}, Val: {}, Unp: {} (${:1.2f}), Bal: {} (${:1.2f})'.format(
                    coin, name, wal, activeWorkers, staleShares, invalidShares, validShares,
                    unpaid, unpaid * price, balance, balance * price))
        else:
            print('{}: \'{}\' {}\n Unc: {} Unp: {}, Tot: {}, Bal: {} (${:1.2f})'.format(
                coin, name, wal, unconfirmed, unpaid, unconfirmed + unpaid,
                balance, balance * price))

        print(' Price: ${:1.5f} Difficulty: {}'.format(price, difficulty))


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
    # start sensor read thread.
    if run_temperature:
        temp.start()

    # loop, sleep 30, rinse, repeat
    while True:
        try:
            # login to hive, if needed, and get farm(s) data
            if not wh.hive_login():
                print('Failed to log in to HiveOS; sleeping for {} seconds...'.format(sleep_seconds))
                wh.invalidate_hive_access_token()
            else:
                # get and process HiveOS farms
                farms = wh.get_farms()
                if not farms:
                    print('Failed to fetch HiveOS farms; sleeping for {} seconds...'.format(sleep_seconds))
                else:
                    for farm in farms:
                        # process HiveOS farm workers
                        process_farm_workers(farm)
                        # get and process HiveOS wallets
                        farm_wallets = wh.get_farm_wallets(farm)
                        process_farm_wallets(farm_wallets)
                    print('======================================================================')

        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            if run_temperature and temp:
                temp.stop()
            sys.exit()
        except Exception as e:
            print('ERROR: unhandled: {}'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        time.sleep(sleep_seconds)


#####################################################################################
## main script entry point
#####################################################################################
if __name__ == '__main__':
    main()
