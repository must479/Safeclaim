# This script fetches block rewards from Etherscan.
# This includes uncle rewards.

from datetime import datetime
import csv

from etherscan.accounts import Account
from etherscan.client import EmptyResponse


ETHERSCAN_API_KEY = ''
BLOCK_TYPES = ['blocks', 'uncles']

MINER_SAFES = ['0xf20b338752976878754518183873602902360704']  # Use https://dune.com/queries/638270 to get this list.
OUTPUT_FILENAME_SQL = '../csv/rewards.sql'
OUTPUT_FILENAME_CSV = '../csv/rewards.csv'
page_size = 10000  # Etherscan page size

data = {}

# Fetch data
for address in MINER_SAFES:
    etherscan_api = Account(address=address, api_key=ETHERSCAN_API_KEY)

    data[address] = {}

    for block_type in BLOCK_TYPES:
        page = 1
        while True:
            print('Safe: {}, block type: {}, page: {}'.format(address, block_type, page))
            try:
                rewards = etherscan_api.get_blocks_mined_page(  
                    blocktype=block_type, 
                    page=page,
                    offset=page_size)
            except EmptyResponse:
                break
            
            if len(rewards) == 0:
                break
                
            for reward in rewards:
                block_number = int(reward['blockNumber'])

                if block_number < 6775227 or block_number > 14168325:
                    continue

                day = str(datetime.fromtimestamp(int(reward['timeStamp'])).date())
                balance_change = int(reward['blockReward'])

                if not day in data[address]:
                    data[address][day] = 0
                
                data[address][day] += balance_change
                
                

            page += 1

# Output for usage in SQL
with open(OUTPUT_FILENAME_SQL, 'w') as outfile:
    
    for address in data.keys():
        values = []
        for day in data[address].keys():
            values.append("\t('\\{}'::bytea, '{}'::date,{})".format(address[1:], day, data[address][day]))
    outfile.write('SELECT * FROM (VALUES \n')
    outfile.write(",\n".join(values))
    outfile.write('\n) AS t (address,day,balance_change)')

# Output as CSV
with open(OUTPUT_FILENAME_CSV, 'w') as outfile:
    writer = csv.writer(outfile, delimiter=',')
    for address in data.keys():
        for day in data[address].keys():
            writer.writerow(['\\{}'.format(address[1:]), day, data[address][day]])