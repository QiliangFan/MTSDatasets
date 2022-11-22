
import os
from glob import glob
import pandas as pd
import pretty_errors
from multiprocessing import Pool
import gc
import numpy as np
from itertools import product

# 数据缺失太多的pod，
not_used = ["paymentservice-2", "adservice2-0", "adservice-0"]

def process_pod_metric(date: str, pod_name_with_prefix: str):
    metric_root = os.path.join(data_root, date, "metric")
    pod_data_root = os.path.join(metric_root, "container")
    pod_metric_files = glob(os.path.join(pod_data_root, "*.csv"))
    out_root = os.path.join("output", date)
    pod_out_root = os.path.join(out_root, "pod")
    if not os.path.exists(pod_out_root):
        os.makedirs(pod_out_root, exist_ok=True)
    pod_name = pod_name_with_prefix.split(".")[1]
    out_file = os.path.join(pod_out_root, f"{pod_name}.csv")

    print(f"{date}: pod-{pod_name}\t", end="")
    if not os.path.exists(out_file) and pod_name not in not_used:
        # seperately generate data for each pod
        metric_dt = None
        for metric_file in pod_metric_files:
            pod_metric = pd.read_csv(metric_file, dtype={"value": np.float32}, engine="pyarrow")
            pod_metric = pod_metric[pod_metric["cmdb_id"] == pod_name_with_prefix]

            metric_names = set(pod_metric["kpi_name"].tolist())
            for metric_name in metric_names:
                seg = pod_metric[pod_metric["kpi_name"] == metric_name]

                to_be_merged_dt = pd.DataFrame(seg[["timestamp", "value"]], index=None)
                del seg
                to_be_merged_dt = to_be_merged_dt.rename(columns={"value": f"{metric_name}"})

                if metric_dt is None:
                    metric_dt = to_be_merged_dt
                else:
                    """
                    有的指标其时间戳相差非常大，如果直接用merge，内存占用极其巨大
                    因此只推荐left outer join， 而不应该用outer join
                    [paymentservice-2, ] 指标缺失太多，不宜使用

                    """
                    metric_dt = pd.merge(metric_dt, to_be_merged_dt, how="left", on="timestamp")
                del to_be_merged_dt
                

        assert metric_dt is not None
        metric_dt.to_csv(out_file, index=False)
        
        del metric_dt
        gc.collect()
        print("** ", end="")
    print("Bingo!")

def main():
    dates = ["2022-03-29-cloudbed1", "2022-03-30-cloudbed1", "2022-04-01-cloudbed1"]
    # for date in dates:
    #     metric_root = os.path.join(data_root, date, "metric")
    #     out_root = os.path.join("output", date)
        
    #     #####################################
    #     # service metric
    #     # sr: Sender Report
    #     # rr: Receiver Report
    #     # mrt: Mean Response Time
    #     #####################################
    #     service_data_root = os.path.join(metric_root, "service")
    #     service_metric_files = glob(os.path.join(service_data_root, "*.csv"))
    #     service_out_root = os.path.join(out_root, "service")
    #     if not os.path.exists(service_out_root):
    #         os.makedirs(service_out_root, exist_ok=True)
    #     for service_metric in service_metric_files:
    #         dt = pd.read_csv(service_metric)
    #         for group_name, group_dt in dt.groupby(by="service"):
    #             group_dt = group_dt[["timestamp", "rr", "sr", "mrt"]]
    #             group_dt = group_dt.sort_values(by="timestamp", ignore_index=True)
    #             group_name = str(group_name)
    #             out_file = os.path.join(service_out_root, f"{group_name}.csv")
    #             group_dt.to_csv(out_file, index=False)
    #     print(f"{date}: service")


    # #####################################
    # # node
    # # sr: Sender Report
    # # rr: Receiver Report
    # # mrt: Mean Response Time
    # # 注意由于存在missing data，处理方式就不能很简单了
    # # node之间公共的指标也不同，因此选最大公共子集
    # #####################################
    # # 只有node-5和node-6有服务部署
    # valid_nodes = ["node-5", "node-6"]
    # valid_metric_sets = set()

    # # 获取指标的最大公共子集
    # for date in dates:
    #     metric_root = os.path.join(data_root, date, "metric")
    #     node_data_root = os.path.join(metric_root, "node")
    #     node_metric_files = glob(os.path.join(node_data_root, "*.csv"))
    #     out_root = os.path.join("output", date)

    #     for node_metric in node_metric_files:
    #         node_dt = pd.read_csv(node_metric)
    #         for node_name, group_dt in node_dt.groupby(by="cmdb_id"):
    #             if node_name not in valid_nodes:
    #                 continue
    #             metrics = set(group_dt["kpi_name"].to_list())
    #             if len(valid_metric_sets) == 0:
    #                 valid_metric_sets |= metrics
    #             else:
    #                 valid_metric_sets &= metrics

    # for date in dates:
    #     metric_root = os.path.join(data_root, date, "metric")
    #     node_data_root = os.path.join(metric_root, "node")
    #     node_metric_files = glob(os.path.join(node_data_root, "*.csv"))
    #     out_root = os.path.join("output", date)
    #     node_output_root = os.path.join(out_root, "node")
    #     if not os.path.exists(node_output_root):
    #         os.makedirs(node_output_root)
        
    #     for node_metric in node_metric_files:
    #         node_dt = pd.read_csv(node_metric)
    #         for node_name, group_dt in node_dt.groupby(by="cmdb_id"):
    #             if node_name not in valid_nodes:
    #                 continue
    #             metrics = OrderedDict()
    #             ts_list = set(sorted(group_dt["timestamp"].tolist()))
    #             metric_names = set(group_dt["kpi_name"].tolist()) & valid_metric_sets

    #             metrics["timestamp"] = []
    #             for metric_name in metric_names:
    #                 metrics[metric_name] = []
                
    #             for ts in ts_list:
    #                 metrics["timestamp"].append(ts)
    #                 seg = group_dt[group_dt["timestamp"] == ts]
    #                 for metric_name in metric_names:
    #                     if metric_name in seg["kpi_name"].tolist():
    #                         metrics[metric_name].append(seg[seg["kpi_name"] == metric_name]["value"].item())
    #                     else:
    #                         metrics[metric_name].append(-1)
    #             dt = pd.DataFrame(metrics)
    #             out_file = os.path.join(node_output_root, f"{node_name}.csv")
    #             dt.to_csv(out_file, index=False)
    #             print(f"metric num: {len(metrics.keys())-1}")
    #     print(f"{date}: node")

    #####################################
    # pods' metrics
    # 
    #####################################
    # get all pods names
    metric_root = os.path.join(data_root, dates[0], "metric")
    pod_data_root = os.path.join(metric_root, "container")
    pod_metric_files = glob(os.path.join(pod_data_root, "*.csv"))

    all_pods = set()
    for metric_file in pod_metric_files:
        pod_metric = pd.read_csv(metric_file)
        cmdb_ids = set(pod_metric["cmdb_id"].tolist())
        all_pods |= cmdb_ids

    with Pool(1) as pool:
        params = [(date,pod_name) for date, pod_name in product(dates, all_pods)]
        pool.starmap(process_pod_metric, params)


if __name__ == "__main__":
    data_root = "/home/fanqiliang/data/MTS/AIops2022/data"
    
    main()
