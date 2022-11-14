import os
from glob import glob
import pandas as pd
import numpy as np
import json

def main():
    csvs = glob(os.path.join(root, "*.csv"))
    map = {}
    for csv in csvs:
        dt = pd.read_csv(csv)
        dt = dt[["cmdb_id"]]
        dt.drop_duplicates(inplace=True)
        for id in dt["cmdb_id"].values:
            node, service = id.split(".")
            service = service.split("-")[0]
            if node in map:
                map[node].add(service)
            else:
                map[node] = set()
                map[node].add(service)

    for key in map:
        map[key] = list(map[key])
    json.dump(map, open(out_file, "w"), indent=4)



if __name__ == "__main__":
    root = "/home/fanqiliang/data/MTS/AIops2022/data/2022-03-29-cloudbed1/metric/container"
    out_dir = "output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "deploy_status.json")

    main()