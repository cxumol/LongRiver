import requests
import re
import json
import csv
from os import path,listdir
import pathlib
import shutil

####### slice data to correlated months
from datetime import datetime, timezone, timedelta
# Why use the running time rather than latest data timestamp? 
# Because year-month have to be known at first due to determine file storage location in our program's logic
yr_mth = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m")

store_data_folder = "./data/%s/"%yr_mth
store_data_full = store_data_folder + "LongRiver.json"

pathlib.Path(store_data_folder).mkdir(parents=True, exist_ok=True) # "$mkdir -p" equalavant

# hotfix: move data file from old location to new one
for fn in listdir("./data/"):
    if fn.endswith(".csv") or fn.endswith(".json"):
        thismove=shutil.move(path.join('./data/', fn) , store_data_folder)
        print("MOVE", thismove)

####### end of slice data to correlated months

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


with open(store_data_full, 'w') as f:
    json.dump(LongRiverData, f, ensure_ascii=False, indent=0)
