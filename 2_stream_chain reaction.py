from stream_start_new import run_streamfront
import pandas as pd
import os

# match each tributary stream to corresponding streamfronts

tributary_map = {
    'hongje_4' : 'bulgwang',
    'anyang_2' : 'mokgam',
    'anyang_3' : 'dorim',
    'tan_2' : 'yangje',
    'jungrang_4' : 'ui',
    'jungrang_5' : 'cheonggye'
}

tributary_output = {
    name: run_streamfront(name)['qout']
    for name in tributary_map.values()
}

def final_stream_discharge(waterfront_name, n_segments):

    upstream_q = None
    results = []
    csv_path = "assign desired directory of CSV output file"

    for i in range(1, n_segments + 1):
        segment_name = f"{waterfront_name}_{i}"
        current_upstream = upstream_q

        if segment_name in tributary_map:
            trib_name = tributary_map[segment_name]
            trib_q = tributary_output[trib_name]
            if upstream_q is None:
                current_upstream = trib_q
            else:
                current_upstream = {
                    t:current_upstream[t] + trib_q[t]
                    for t in range(1, 25)
                }

        res= run_streamfront(segment_name, current_upstream)
        q1 = res["qout"]
        bc1 = res["buffer_capacity"]

        upstream_q = q1
        results.append({
            "waterfront_id": segment_name,
            "buffer_capacity": bc1,
            "qout": q1
        })

    df = pd.DataFrame(results)
    df["buffer_capacity"] = pd.to_numeric(df["buffer_capacity"], errors="coerce")
    df = df.drop(columns = ["qout"])

    df.to_csv(
        csv_path,
        mode="a",  # append
        header=not os.path.exists(csv_path),  # write header only once
        index=False
    )
    return upstream_q      # upstream_q in order to feed into river, results to plot

# -----------------------------------check hydrograph (discharge flow rate over time) of waterfronts ----------------------------------
import matplotlib.pyplot as plt

def plot_all_qout(results, title="Outflow per segment"):
    plt.figure(figsize=(10, 5))

    for res in results:
        times = list(res["qout"].keys())
        discharge = list(res["qout"].values())

        plt.plot(times, discharge, marker='o', label=res["waterfront_id"])

    plt.xlabel("Time (hour)")
    plt.ylabel("Discharge (m³/hr)")
    plt.title(title)
    plt.xticks(range(1, 25))
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    final_q = final_stream_discharge('anyang', 3)
    plot_all_qout(final_q)