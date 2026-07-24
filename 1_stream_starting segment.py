from math import sqrt
import geopandas as gpd

def run_streamfront(waterfront_name, upstream = None, min_depth = 0.01):

    if upstream is None:
        upstream = {t:0 for t in range(1,25)}

    # import landuse data
    landuse_file = "directory for land use data clipped for each catchment basin"
    gdf = gpd.read_file(landuse_file, layer=waterfront_name)
    gdf['area'] = gdf.geometry.area
    landuse_area = gdf.groupby("type")["area"].sum()

    # runoff coefficients
    runoff_c = {
        'commercial': 0.725,    # total median value
        'residential': 0.55,    # excludes single houses
        'mobility': 0.825,      # only from asphalt
        'agriculture': 0.4,     # sandy soil
        'soil': 0.45,           # uncultivated farmland
        'grass': 0.125,         # average slope of sandy soil
        'forest': 0.55,         # total median value
        'wetland': 0.75,        # cultivated rice fields
        'public': 0.6,          # non-central commercial
        'industrial': 0.75      # dense
    }

    # calculate sum of (runoff coefficient* area per surface type)
    runoff_sum = sum(landuse_area[lu] * runoff_c[lu]
                     for lu in landuse_area.index
                     if lu in runoff_c)

    # import waterfront length from files
    length_gpkg = "directory to stream centerline data properly segmented according to waterfront definition"

    gdf_length = gpd.read_file(length_gpkg)
    obj = gdf_length[gdf_length["waterfront_id"] == waterfront_name]
    if obj.empty:
        raise ValueError(f"Waterfront {waterfront_name} not found")

    # storage parameters
    length = obj["length"].iloc[0]
    storage_vol_max = obj["storage_vol"].iloc[0]
    slope = obj["slope"].iloc[0]
    n = 0.014

    # Upstream cross section
    b_up = obj["b_up"].iloc[0]
    z_1_up = obj["z1_up"].iloc[0]
    z_2_up = obj["z2_up"].iloc[0]

    # Discharge point cross section
    b = obj["b"].iloc[0]
    z_1 = obj["z1"].iloc[0]
    z_2 = obj["z2"].iloc[0]

    # Averaged section
    b_avg = (b_up + b) / 2
    z_1_avg = (z_1 + z_1_up) / 2
    z_2_avg = (z_2 + z_2_up) / 2

    # rainfall intensity
    def r_intensity(t):
        d = {1:4.73,
             2:9.36,
             3:10.08,
             4:10.44,
             5:11.00,
             6:12.74,
             7:15.35,
             8:16.68,
             9:27.68,
             10:34.71,
             11:63.00,
             12:113.20,
             13:47.00,
             14:30.60,
             15:17.27,
             16:16.15,
             17:13.90,
             18:11.32,
             19:10.71,
             20:10.18,
             21:9.95,
             22:8.76,
             23:4.49,
             24:4.28}
        return d[t]


    # inflow
    def q_in(t):
        # print("t:", t, "upstream.get(t,0):", upstream.get(t, 0))
        rainfall_runoff = r_intensity(t) / 1000 * runoff_sum
        return rainfall_runoff + upstream.get(t, 0)

    T = 24
    storage = [0]*(T+1)
    qout = [0]*(T+1)
    overflow = [0]*(T+1)

    for t in range(2,T+1):
        # compute storage first
        storage[t] = max(0, min(storage_vol_max, q_in(t-1) + max(storage[t - 1] - qout[t-1], 0) if t > 1 else 0))

        # average section area at time t
        sec_area_t = storage[t-1] / length

        # depth from averaged trapezoid
        depth_t = (-b_avg + sqrt(b_avg ** 2 +
                               2 * sec_area_t * (z_1_avg + z_2_avg))) / (z_1_avg + z_2_avg)

        depth_t = max(depth_t, min_depth)

        # apply averaged depth to discharge point
        discharge_area_t = (z_1+z_2)/2 * depth_t**2 + b*depth_t

        wet_p_t = b + depth_t*(sqrt(1+z_1**2) + sqrt(1+z_2**2))

        r = discharge_area_t / wet_p_t if wet_p_t>0 else 0

        u_t = 3600/n * sqrt(slope) * r**(2/3) if r>0 else 0

        qout[t] = u_t * discharge_area_t

        overflow[t] = max(
            0,
            q_in(t) - qout[t] - (storage_vol_max - storage[t - 1])
        )
    overflow_sum = sum(overflow[1:])
    rainfall_sum = sum(q_in(t) for t in range(1, T + 1))
    buffer_capacity = 1 - overflow_sum / rainfall_sum

    print('buffer capacity of', waterfront_name, 'is', buffer_capacity)
    return {'qout':{t:qout[t] for t in range(1,T+1)},
            'buffer_capacity':buffer_capacity}

# ----------------------------------check hydrograph (discharge flow rate over time) of waterfront---------------------------------

import matplotlib.pyplot as plt
def plot_qout(data, title="Outflow hydrograph"):
    qout = data['qout']
    times = list(qout.keys())
    discharge = list(qout.values())

    plt.figure(figsize=(10, 5))
    plt.plot(times, discharge, marker='o', linestyle='-', color='blue')
    plt.xlabel("Time (hour)")
    plt.ylabel("Discharge (m³/hr)")  # adjust units if needed
    plt.title(title)
    plt.grid(True)
    plt.xticks(range(1, 25))  # show every hour
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print(run_streamfront('bulgwang'))
    plot_qout(run_streamfront('bulgwang'))

