import requests
import re
import json
import csv
from os import path

store_data_folder = "./data/"
store_data_full = store_data_folder + "LongRiver.json"

def write_csv_header(data,fname_prefix):
    with open('{}.csv'.format(fname_prefix), 'w', newline='') as f:
        headers = list(data.keys())
        csv.writer(f).writerow(headers)

def write_csv_row(data,fname_prefix):
    with open('{}.csv'.format(fname_prefix), 'a', newline='') as f:
        csv.writer(f).writerow(data.values())

# LongRiverData wil be a json of summary
if not path.isfile(store_data_full):
    LongRiverData = {}
else:
    with open(store_data_full, 'r') as f:
        LongRiverData = json.load(f)

html = requests.get('http://www.cjh.com.cn/sqindex.html').text
river_now = json.loads(re.findall("var sssq = (.*);",html)[0])
print(river_now)


for station in river_now:
    fname_prefix = store_data_folder + '_'.join([station['rvnm'], station['stnm']])

    if fname_prefix not in LongRiverData:
        LongRiverData[fname_prefix] = []
    # skip if update time has not yet changed
    if LongRiverData[fname_prefix] and LongRiverData[fname_prefix][-1]['tm'] == station['tm']:
        continue
    LongRiverData[fname_prefix].append(station)
    

    if not path.isfile('{}.csv'.format(fname_prefix)):
        write_csv_header(station, fname_prefix)
    write_csv_row(station, fname_prefix)

    if fname_prefix not in LongRiverData:
        LongRiverData[fname_prefix] = []
    LongRiverData[fname_prefix].append(station)

with open(store_data_full, 'w') as f:
    json.dump(LongRiverData, f, ensure_ascii=False, indent=0)
