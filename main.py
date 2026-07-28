import json
import csv
from os import path,listdir
import pathlib
import shutil

from longriver import fetch_all_river_data


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
    with open("{}.csv".format(fname_prefix), "w", newline="", encoding="utf-8") as f:
        headers = list(data.keys())
        csv.writer(f).writerow(headers)

def write_csv_row(data,fname_prefix):
    with open("{}.csv".format(fname_prefix), "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(data.values())

# LongRiverData wil be a json of summary
if not path.isfile(store_data_full):
    LongRiverData = {}
else:
    with open(store_data_full, "r", encoding="utf-8") as f:
        LongRiverData = json.load(f)

data = fetch_all_river_data()

print(data)

for station in data:
    fname_prefix = store_data_folder + '_'.join([station['rvnm'], station['stnm']])

    if fname_prefix not in LongRiverData:
        LongRiverData[fname_prefix] = []
    # Sources overlap, so skip observations already stored at the same station time.
    known_times = {item['tm'] for item in LongRiverData[fname_prefix]}
    if station['tm'] in known_times:
        continue
    LongRiverData[fname_prefix].append(station)

    if not path.isfile('{}.csv'.format(fname_prefix)):
        write_csv_header(station, fname_prefix)
    write_csv_row(station, fname_prefix)


with open(store_data_full, "w", encoding="utf-8") as f:
    json.dump(LongRiverData, f, ensure_ascii=False, indent=0)
