from river_start_new import run_riverfront
from stream_chain_new import final_stream_discharge
import pandas as pd
import os

results = []
csv_path = "assign desired directory of CSV output file"

# riverfront 1 (no upstream input)
q1_out = run_riverfront('hangang_1')
q1_n = q1_out['qout_n']
q1_s = q1_out['qout_s']


results.extend([
            {"waterfront_id": 'hangang_1n',
        "buffer_capacity": q1_out['buffer_capacity_n']},
    {"waterfront_id": 'hangang_1s',
     "buffer_capacity": q1_out['buffer_capacity_s']}])

# riverfront 2 (receives riverfront 1)
tan = final_stream_discharge('tan', 2)
upstream_2_n = [q1_n]
upstream_2_s = [q1_s, tan]
q2_out = run_riverfront('hangang_2', upstream_n=upstream_2_n, upstream_s=upstream_2_s)
q2_n = q2_out['qout_n']
q2_s = q2_out['qout_s']

results.extend([
            {"waterfront_id": 'hangang_2n',
        "buffer_capacity": q2_out['buffer_capacity_n']},
    {"waterfront_id": 'hangang_2s',
     "buffer_capacity": q2_out['buffer_capacity_s']}])

# riverfront 3 (receives riverfront 2)
jungrang = final_stream_discharge('jungrang', 5)
upstream_3_n = [q2_n, jungrang]
upstream_3_s = [q2_s]
q3_out = run_riverfront('hangang_3', upstream_n=upstream_3_n, upstream_s=upstream_3_s)
q3_n = q3_out['qout_n']
q3_s = q3_out['qout_s']

results.extend([
            {"waterfront_id": 'hangang_3n',
        "buffer_capacity": q3_out['buffer_capacity_n']},
    {"waterfront_id": 'hangang_3s',
     "buffer_capacity": q3_out['buffer_capacity_s']}])

# riverfront 4 (receives riverfront 3)
upstream_4_n = [q3_n]
upstream_4_s = [q3_s]
q4_out = run_riverfront('hangang_4', upstream_n=upstream_4_n, upstream_s=upstream_4_s)
q4_n = q4_out['qout_n']
q4_s = q4_out['qout_s']

results.extend([
            {"waterfront_id": 'hangang_4n',
        "buffer_capacity": q4_out['buffer_capacity_n']},
    {"waterfront_id": 'hangang_4s',
     "buffer_capacity": q4_out['buffer_capacity_s']}])

# riverfront 5 (receives riverfront 4)
upstream_5_n = [q4_n]
upstream_5_s = [q4_s]
q5_out = run_riverfront('hangang_5', upstream_n=upstream_5_n, upstream_s=upstream_5_s)
q5_n = q5_out['qout_n']
q5_s = q5_out['qout_s']

results.extend([
            {"waterfront_id": 'hangang_5n',
        "buffer_capacity": q5_out['buffer_capacity_n']},
    {"waterfront_id": 'hangang_5s',
     "buffer_capacity": q5_out['buffer_capacity_s']}])

# riverfront 6 (receives riverfront 5)
hongje = final_stream_discharge('hongje', 4)
anyang = final_stream_discharge('anyang', 3)
upstream_6_n = [q5_n, hongje]
upstream_6_s = [q5_s, anyang]
q6_out = run_riverfront('hangang_6', upstream_n=upstream_6_n, upstream_s=upstream_6_s)
q6_n = q6_out['qout_n']
q6_s = q6_out['qout_s']

results.extend([
            {"waterfront_id": 'hangang_6n',
        "buffer_capacity": q6_out['buffer_capacity_n']},
    {"waterfront_id": 'hangang_6s',
     "buffer_capacity": q6_out['buffer_capacity_s']}])


# write to CSV
df = pd.DataFrame(results)
df["buffer_capacity"] = pd.to_numeric(df["buffer_capacity"], errors="coerce")

df.to_csv(
    csv_path,
    mode="a",  # append
    header=not os.path.exists(csv_path),  # write header only once
    index=False
)

df = pd.read_csv(csv_path)
df["buffer_capacity"] = pd.to_numeric(df["buffer_capacity"], errors="coerce")
df = df.drop_duplicates()
df.to_csv(csv_path, index=False)