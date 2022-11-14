"""
Only care about the data of cloudbed1
"""

import numpy as np
import pandas as pd
import os
from glob import glob
from graphviz import Digraph
from tqdm import tqdm 
from multiprocessing import Pool
import re

def gen_call_graph(trace_file, name: str):
    save_dir = os.path.join("output", name)
    call_map_file = os.path.join("output", "call_map.txt")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    
    if not os.path.exists(call_map_file):

        trace = pd.read_csv(trace_file)
        trace.sort_values(by="timestamp", inplace=True)
        trace = trace[["cmdb_id", "span_id", "parent_span"]]

        call_map = set()
        total_len = len(trace)

        for idx, row in tqdm(enumerate(trace.itertuples()), total=total_len):
            row = row._asdict()
            cmdb = row["cmdb_id"]
            parent_span = row["parent_span"]
            lower_span = 600 # some trace is long enough...
            upper_span = 50 # for the sake of the points with the same timestamp
            if type(parent_span) != float:
                parent_span = str(parent_span)
                lower_bound = idx - lower_span if idx - lower_span > 0 else 0
                upper_bound = idx + upper_span if idx + upper_span < total_len - 1 else total_len - 1
                search_duration = trace[lower_bound:upper_bound]
                parent_list = search_duration[search_duration["span_id"] == parent_span]["cmdb_id"]
                if len(parent_list) == 1:
                    parent_cmdb = parent_list.item()
                    call_map.add((parent_cmdb, cmdb))

                # As some span is really missing, there is no need to care about it 

                # else:
                #     print(parent_span)
                #     raise ValueError(parent_list)
            call_map_fp = open(call_map_file, "w")
            for src, dst in call_map:
                if src != dst:
                    print(src, dst, sep=",", file=call_map_fp)
                    print(src, dst, sep=",")
            call_map_fp.flush()
            call_map_fp.close()
    
    import json
    deploy_map = json.load(open(os.path.join("output", "deploy_status.json")))
    # 每个service都有多个实例，但是如果A->B存在调用关系，并非AX到所有BX都有调用链，因为调用链采集总是存在缺漏，不完备
    dot = Digraph("Call Graph", format="png", strict=True)

    call_map = np.loadtxt(call_map_file, delimiter=",", dtype=str).tolist()
    # call_map = map(lambda x: (re.sub(r"[0-9]", "", x[0].split("-")[0]), re.sub(r"[0-9]", "", x[1].split("-")[0])), call_map)
    call_map = map(lambda x: (x[0].split("-")[0], x[1].split("-")[0]), call_map)

    for key in deploy_map:
        with dot.subgraph(name=key) as sub:
            sub.attr(label=key)
            sub.attr(color="blue")
            sub.attr(style='filled', color='lightgrey')
            for src, dst in call_map:
                if src != dst:
                    if src in deploy_map[key] and dst in deploy_map[key]:
                        sub.edge(src, dst)
                    else:
                        dot.edge(src, dst)
    
    dot.render(directory="output")


def main(dst_day: str, name: str):
    trace_file = glob(os.path.join(dst_day, "**", "trace_jaeger-span.csv"), recursive=True)
    assert len(trace_file) == 1
    trace_file = trace_file[0]
    gen_call_graph(trace_file, name)


if __name__ == "__main__":
    data_root = "/home/fanqiliang/data/MTS/AIops2022/data"
    days = [
        "2022-03-29-cloudbed1",
        "2022-03-30-cloudbed1",
        "2022-04-01-cloudbed1",
    ]

    for day in days:
        main(os.path.join(data_root, day), name=day)
        break
