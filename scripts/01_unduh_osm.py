"""Langkah 2a: unduh jalan dan toko dari OSM, simpan ke folder data/.
Butuh internet dan bisa lama. Hasil disimpan, jadi cukup dijalankan SEKALI."""
import sys, os, pathlib
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)
import osmnx as ox
from ga_rute import data

ox.settings.use_cache = True          # respons OSM disimpan di folder cache/
ox.settings.log_console = True
ox.settings.requests_timeout = 300

poligon, gdf = data.unduh_batas_kota()

print("Mengunduh toko ...")
toko = data.unduh_toko(poligon)
for merek, df in toko.items():
    df.to_csv(f"data/{merek}.csv", index=False)
    print(f"  {merek}: {len(df)} gerai  (tag shop: {df['shop'].value_counts().to_dict()})")

print("Mengunduh jaringan jalan (bagian paling lama) ...")
G = data.unduh_jalan(gdf)
ox.save_graphml(G, "data/jalan_bandung.graphml")
print(f"Graf jalan: {len(G.nodes)} simpul, {len(G.edges)} sisi")
print("Selesai. Lanjut: python scripts/02_bangun_matriks.py")
