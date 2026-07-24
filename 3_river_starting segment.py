from math import sqrt
import geopandas as gpd

def run_riverfront(waterfront_name, upstream_n=None, upstream_s=None):

    if upstream_n is None:
        upstream_n = []
    if upstream_s is None:
        upstream_s = []

    north_name = waterfront_name + 'n'
    south_name = waterfront_name + 's'
    river_name = waterfront_name + 'r'

    landuse_file = "directory for land use data clipped for each catchment basin"

    gdf_n = gpd.read_file(landuse_file, layer=north_name)
    gdf_n['area'] = gdf_n.geometry.area
    landuse_area_n = gdf_n.groupby("type")["area"].sum()
    gdf_s = gpd.read_file(landuse_file, layer=south_name)
    gdf_s['area'] = gdf_s.geometry.area
    landuse_area_s = gdf_s.groupby("type")["area"].sum()
    gdf_r = gpd.read_file(landuse_file, layer=river_name)
    gdf_r['area'] = gdf_r.geometry.area
    landuse_area_r = gdf_r.groupby("type")["area"].sum()

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
    runoff_sum_n = sum(landuse_area_n[lu] * runoff_c[lu]
                       for lu in landuse_area_n.index
                       if lu in runoff_c)
    runoff_sum_s = sum(landuse_area_s[lu] * runoff_c[lu]
                       for lu in landuse_area_s.index
                       if lu in runoff_c)
    runoff_sum_r = sum(landuse_area_r[lu] * runoff_c[lu]
                       for lu in landuse_area_r.index
                       if lu in runoff_c)


    north_ratio = 0.52
    south_ratio = 0.48
    north_river_runoff = north_ratio * runoff_sum_r
    south_river_runoff = south_ratio * runoff_sum_r

    # import waterfront length from files
    length_gpkg = "directory to stream centerline data properly segmented according to waterfront definition"

    gdf_length = gpd.read_file(length_gpkg)
    obj = gdf_length[gdf_length["waterfront_id"] == waterfront_name]
    if obj.empty:
        raise ValueError(f"Waterfront {waterfront_name} not found")

    # storage parameters
    length = obj["length"].iloc[0]
    storage_vol_max = obj["storage_vol"].iloc[0]
    n = 0.014
    slope = obj["slope"].iloc[0]

    # Upstream cross section
    b_up = obj["b_up"].iloc[0]
    z_1_up = obj["z1_up"].iloc[0]
    z_2_up = obj["z2_up"].iloc[0]

    # Discharge point cross section
    b = obj["b"].iloc[0]
    z_1 = obj["z1"].iloc[0]
    z_2 = obj["z2"].iloc[0]

    def upstream_total_n(t):
        return sum(q[t] for q in upstream_n)
    def upstream_total_s(t):
        return sum(q[t] for q in upstream_s)


    # Averaged section
    b_avg = (b_up + b) / 2
    z_1_avg = (z_1 + z_1_up) / 2
    z_2_avg = (z_2 + z_2_up) / 2
    sec_area_avg_max = storage_vol_max / length

    north_sec_area_max = sec_area_avg_max * north_ratio
    south_sec_area_max = sec_area_avg_max * south_ratio

    # rainfall intensity
    def r_intensity(t):
        d = {1:10.44,
             2:10.89,
             3:11.53,
             4:12.29,
             5:15.97,
             6:21.52,
             7:22.55,
             8:23.87,
             9:28.15,
             10:36.55,
             11:80.00,
             12:139.40,
             13:60.50,
             14:31.60,
             15:25.90,
             16:23.73,
             17:22.23,
             18:16.73,
             19:15.30,
             20:11.90,
             21:11.20,
             22:10.59,
             23:9.98,
             24:9.57}
        return d[t]


    # inflow
    def q_in_n(t):
        rainfall_runoff = r_intensity(t)/1000 * (runoff_sum_n + north_river_runoff)
        return rainfall_runoff + upstream_total_n(t)

    def q_in_s(t):
        rainfall_runoff = r_intensity(t)/1000 * (runoff_sum_s + south_river_runoff)
        return rainfall_runoff + upstream_total_s(t)

    storage_max_n = storage_vol_max * north_ratio
    storage_max_s = storage_vol_max * south_ratio

    T = 24
    storage_n = [0] * (T + 1)
    storage_s = [0] * (T + 1)

    qout_n = [0] * (T + 1)
    qout_s = [0] * (T + 1)

    overflow_n = [0] * (T + 1)
    overflow_s = [0] * (T + 1)

    for t in range(2, T + 1):
        # ---------- NORTH ----------
        # average section area and depth
        sec_area_n = storage_n[t-1] / length

        depth_n = (-b_avg + sqrt(b_avg ** 2 + 2 * sec_area_n * (z_1_avg + z_2_avg))) / (z_1_avg + z_2_avg)
        depth_n_max = (-b_avg + sqrt(b_avg ** 2 + 2 * north_sec_area_max * (z_1_avg + z_2_avg))) / (z_1_avg + z_2_avg)
        depth_n = min(depth_n_max, max(depth_n, 0))

        # discharge point
        area_n = (z_1 + z_2) / 2 * depth_n ** 2 + b * depth_n
        wet_p_n = b + depth_n * (sqrt(1 + z_1 ** 2) + sqrt(1 + z_2 ** 2))

        r_n = area_n / wet_p_n if wet_p_n > 0 else 0
        u_n = 3600 / n * sqrt(slope) * r_n ** (2 / 3) if r_n > 0 else 0

        qout_n[t] = u_n * area_n

        storage_n[t] = max(0, min(storage_max_n,q_in_n(t - 1) + max(0, storage_n[t - 1] +  - qout_n[t - 1])))

        overflow_n[t] = max(0, q_in_n(t) - qout_n[t] - (storage_max_n - storage_n[t - 1]))

        # ---------- SOUTH ----------
        sec_area_s = storage_s[t-1] / length

        depth_s = (-b_avg + sqrt(b_avg ** 2 + 2 * sec_area_s * (z_1_avg + z_2_avg))) / (z_1_avg + z_2_avg)
        depth_s_max = (-b_avg + sqrt(b_avg ** 2 + 2 * south_sec_area_max * (z_1_avg + z_2_avg))) / (z_1_avg + z_2_avg)

        depth_s = min(depth_s_max, max(depth_s, 0))

        area_s = (z_1 + z_2) / 2 * depth_s ** 2 + b * depth_s
        wet_p_s = b + depth_s * (sqrt(1 + z_1 ** 2) + sqrt(1 + z_2 ** 2))

        r_s = area_s / wet_p_s if wet_p_s > 0 else 0
        u_s = 3600 / n * sqrt(slope) * r_s ** (2 / 3) if r_s > 0 else 0

        qout_s[t] = u_s * area_s

        storage_s[t] = max(0, min(storage_max_s, q_in_s(t - 1) + max(0, storage_s[t - 1] +  - qout_s[t - 1])))

        overflow_s[t] = max(
            0,
            q_in_s(t) - qout_s[t] - (storage_max_s - storage_s[t - 1])
        )
    overflow_sum_n = sum(overflow_n[1:])
    rainfall_sum_n = sum(q_in_n(t) for t in range(1, T + 1))
    buffer_capacity_n = 1 - overflow_sum_n / rainfall_sum_n

    overflow_sum_s = sum(overflow_s[1:])
    rainfall_sum_s = sum(q_in_s(t) for t in range(1, T + 1))
    buffer_capacity_s = 1 - overflow_sum_s / rainfall_sum_s

    qout_n_dict = {t: qout_n[t] for t in range(1, T + 1)}
    qout_s_dict = {t: qout_s[t] for t in range(1, T + 1)}

    print(waterfront_name, 'north buffer capacity :', buffer_capacity_n)
    print(waterfront_name, 'south buffer capacity :', buffer_capacity_s)

    return {'qout_n': qout_n_dict, 'qout_s': qout_s_dict, 'buffer_capacity_n': buffer_capacity_n,'buffer_capacity_s': buffer_capacity_s}

# ----------------------------------check hydrograph (discharge flow rate over time) of waterfront---------------------------------

import matplotlib.pyplot as plt

def plot_qout(data, title="Outflow hydrograph", side='north'):
    if side == 'north':
        part = 'n'
    else: part = 's'

    qout = data['qout_'+part]
    times = list(qout.keys())
    discharge = list(qout.values())

    plt.figure(figsize=(10, 5))
    plt.plot(times, discharge, marker='o', linestyle='-', color='blue')
    plt.xlabel("Time (hour)")
    plt.ylabel("Discharge (m³/s) for " + side)  # adjust units if needed
    plt.title(title)
    plt.grid(True)
    plt.xticks(range(1, 25))  # show every hour
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    run_riverfront('hangang_1')
    plot_qout(run_riverfront('hangang_1'), side ='south')


