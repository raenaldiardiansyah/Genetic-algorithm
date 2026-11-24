import pandas as pd
df = pd.concat([pd.read_csv("hasil/hasil_indomaret.csv"),
                pd.read_csv("hasil/hasil_alfamart.csv")])
kalah = df[df.ga_km > df.nn_km + 1e-9].copy()
kalah["selisih_pct"] = 100 * (kalah.ga_km - kalah.nn_km) / kalah.nn_km
print(len(kalah), "dari", len(df), "skenario: GA lebih panjang dari NN")
print(kalah.groupby("n").selisih_pct.describe().round(2))