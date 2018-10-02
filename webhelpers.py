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

import json
import os
import re
import sys
import requests

# project imports
import secrets

#TODO: what happens when this expires???
access_token = None

########################################################################################################################
## web api getters for zec/eth/verge price, difficulty, wallet, etc.
########################################################################################################################
def web_get(url, json_load=True, headers=None):
    retval = None

    #TODO: timeout neded?
    try:
        r = requests.get(url=url, headers=headers, verify=False)
        if headers:
            return r
        if not json_load:
            return r.text
        retval = json.loads(r.text)
    except Exception as e:
        print 'web_get exception: {}'.format(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return None
        
    return retval

########################################################################################################################
## get_zcash_price - gets latest zcash price
########################################################################################################################
def get_zcash_price():
    data = web_get('https://coinmarketcap.com/currencies/zcash/', json_load=False)
    if data:
        for line in data.splitlines():
            match = re.search('id="quote_price" data-currency-price data-usd="(\d+\.\d+)"', line)
            if match:
                return float(match.group(1))
    return 0.0

########################################################################################################################
## get_zcash_difficulty - gets latest zcash difficulty
########################################################################################################################
def get_zcash_difficulty():
    data = web_get('https://api.zcha.in/v2/mainnet/network')
    if data:
        return data['difficulty']
    return 0.0

########################################################################################################################
## get_eth_price - gets latest eth price
########################################################################################################################
def get_eth_price():
    data = web_get('https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD', json_load=True)
    if data:
        return float(data['USD'])
    return 0.0

########################################################################################################################
## get_eth_difficulty - gets latest eth difficulty
########################################################################################################################
def get_eth_difficulty():
    data = web_get('https://www.etherchain.org/api/basic_stats/', json_load=True)
    if data:
        return float(data['currentStats']['difficulty'])
    return 0.0

########################################################################################################################
## get_verge_price - gets latest verge price
########################################################################################################################
def get_verge_price():
    data = web_get('https://coinmarketcap.com/currencies/verge/', json_load=False)
    if data:
        for line in data.splitlines():
            match = re.search('id="quote_price" data-currency-price data-usd="(\d+\.\d+)"', line)
            if match:
                return float(match.group(1))
    return 0.0

########################################################################################################################
## get_verge_difficulty - gets latest verge difficulty
########################################################################################################################
def get_verge_difficulty():
    data = web_get('https://verge-blockchain.info/api/getdifficulty', json_load=True)
    if data:
        return float(data['proof-of-work'])
    return 0.0

########################################################################################################################
## get_monero_price - gets latest monero price
########################################################################################################################
def get_monero_price():
    data = web_get('https://coinmarketcap.com/currencies/monero/', json_load=False)
    if data:
        for line in data.splitlines():
            match = re.search('id="quote_price" data-currency-price data-usd="(\d+\.\d+)"', line)
            if match:
                return float(match.group(1))
    return 0.0

########################################################################################################################
## get_monero_difficulty - gets latest monero difficulty
########################################################################################################################
def get_monero_difficulty():
    data = web_get('http://moneroblocks.info/api/get_stats/', json_load=True)
    if data:
        return float(data['difficulty'])
    return 0.0

########################################################################################################################
## get_zcash_balance - get balance in zcash wallet
########################################################################################################################
def get_zcash_balance(address):
    data = web_get('https://api.zcha.in/v2/mainnet/accounts/{}'.format(address), json_load=True)
    if data and data['balance']:
        return float(data['balance'])
    return 0.0

########################################################################################################################
## get_eth_balance - get balance in eth wallet
########################################################################################################################
def get_eth_balance(address):
    data = web_get('https://api.gastracker.io/addr/{}'.format(address), json_load=True)
    if data:
        return float(data['balance']['ether'])
    return 0.0

########################################################################################################################
## get_verge_balance - get balance in verege wallet
########################################################################################################################
def get_verge_balance(address):
    return float(web_get('https://verge-blockchain.info/ext/getbalance/{}'.format(address), json_load=False))

########################################################################################################################
## get_zcash_account - get zcash account/pool data
########################################################################################################################
def get_zcash_account(address):
    return web_get('https://api-zcash.flypool.org/miner/:{}/currentstats'.format(address), json_load=True)

########################################################################################################################
## get_eth_account - get eth account/pool data
########################################################################################################################
def get_eth_account(address):
    return web_get('https://api.ethermine.org/miner/{}/dashboard'.format(address), json_load=True)

########################################################################################################################
## get_verge_account - get verge account/pool data
########################################################################################################################
def get_verge_account(address):
    return web_get('https://cryptocartel.one/api/wallet?address={}'.format(address), json_load=True)


#####################################################################################3
## Hive login using name/password to get access token
#####################################################################################3
def hive_login():
    global access_token

    #TODO: verify access token is still good
    #response = web_get('https://api2.hiveos.farm/api/v2/auth/check')
    #print response

    if not access_token:
        url = 'https://api2.hiveos.farm/api/v2/auth/login'
        headers = {'Content-Type': 'application/json'}
        params = {'login':secrets.HIVE_USER,'password':secrets.HIVE_PASS}
        response = requests.post(url, headers=headers, params=params)

        access_token = response.json()['access_token']

    return access_token

########################################################################################################################
## Hive REST API helper
########################################################################################################################
def get_hive_helper(url, obj_array=False):
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(access_token)}
    response_json = web_get(url=url, json_load=False, headers=headers).json()

    if not obj_array:
        return response_json

    ret_objects = []
    for obj in response_json['data']:
        ret_objects.append(obj)

    return ret_objects

#####################################################################################3
## get Hive farms
#####################################################################################3
def get_farms():
    return get_hive_helper('https://api2.hiveos.farm/api/v2/farms', obj_array=True)

#####################################################################################3
## get Hive farm workers
#####################################################################################3
def get_farm_workers(farm):
    return get_hive_helper('https://api2.hiveos.farm/api/v2/farms/{}/workers'.format(farm['id']), obj_array=True)

#####################################################################################3
## get Hive farm wallets
#####################################################################################3
def get_farm_wallets(farm):
    return get_hive_helper('https://api2.hiveos.farm/api/v2/farms/{}/wallets'.format(farm['id']), obj_array=True)

#####################################################################################3
## get Hive worker oc info
#####################################################################################3
def get_worker_oc(farm, worker):
    return get_hive_helper('https://api2.hiveos.farm/api/v2/farms/{}/workers/{}'.format(farm['id'], worker['id']), obj_array=False)


#####################################################################################
## main script entry point
#####################################################################################
if __name__ == "__main__":
    print 'Intended to be exeuted as a HiveOS-Monitor library'

