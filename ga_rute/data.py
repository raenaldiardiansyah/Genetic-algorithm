"""Tahap 2: data OSM -> matriks jarak jalan (Dijkstra, asimetris).

Fungsi matriks (simpul_terdekat, bangun_matriks) hanya butuh graf networkx
dengan atribut simpul x (bujur), y (lintang) dan atribut sisi 'length' (meter),
jadi bisa diuji tanpa internet.
"""
import re
import numpy as np
import pandas as pd
import networkx as nx

KOTA = "Kota Bandung, Jawa Barat, Indonesia"
BUFFER_M = 2000          # buffer jalan di luar batas kota (slide: buffer 2 km)
EPSG_METER = 32748       # UTM zona 48S, dipakai untuk buffer dalam meter
MEREK = {"indomaret": r"indomaret", "alfamart": r"alfamart"}


# ---------------------------------------------------------------- unduh OSM
def unduh_batas_kota():
    import osmnx as ox
    gdf = ox.geocode_to_gdf(KOTA)
    luas_km2 = gdf.to_crs(EPSG_METER).geometry.area.iloc[0] / 1e6
    print(f"Luas poligon hasil geocode: {luas_km2:.0f} km2")
    if not 120 <= luas_km2 <= 220:
        raise RuntimeError(
            "Luas poligon tidak mirip Kota Bandung (sekitar 167 km2). "
            "Kemungkinan Nominatim mengembalikan wilayah lain; cek ox.geocode_to_gdf.")
    return gdf.geometry.iloc[0], gdf


def unduh_jalan(gdf_batas):
    import osmnx as ox
    poligon = (gdf_batas.to_crs(EPSG_METER).buffer(BUFFER_M)
               .to_crs(4326).geometry.iloc[0])
    G = ox.graph_from_polygon(poligon, network_type="drive")
    G = ox.truncate.largest_component(G, strongly=True)
    return G


def unduh_toko(poligon_kota):
    """Kembalikan DataFrame toko (osmid, nama, tag, lat, lon) per merek."""
    import osmnx as ox
    fitur = ox.features_from_polygon(
        poligon_kota, tags={"shop": ["convenience", "supermarket"]})
    fitur = fitur.reset_index()
    for kolom in ("name", "brand", "operator", "shop"):
        if kolom not in fitur.columns:
            fitur[kolom] = ""
    teks = (fitur["name"].fillna("") + " " + fitur["brand"].fillna("") + " "
            + fitur["operator"].fillna("")).str.lower()
    titik = fitur.geometry.representative_point()
    fitur["lon"], fitur["lat"] = titik.x, titik.y
    hasil = {}
    for merek, pola in MEREK.items():
        sel = fitur[teks.str.contains(pola, regex=True)
                    & fitur.geometry.within(poligon_kota)]
        sel = sel[["id", "name", "shop", "lat", "lon"]].rename(columns={"id": "osmid"})
        sel = hapus_duplikat(sel.reset_index(drop=True))
        hasil[merek] = sel
    return hasil


def hapus_duplikat(df, jarak_m=25):
    """Satu toko kadang tercatat dua kali (titik + bangunan). Buang yang < 25 m."""
    if df.empty:
        return df
    x, y = proyeksi_meter(df["lon"].values, df["lat"].values,
                          df["lon"].mean(), df["lat"].mean())
    simpan = []
    for i in range(len(df)):
        if all((x[i] - x[j]) ** 2 + (y[i] - y[j]) ** 2 > jarak_m ** 2 for j in simpan):
            simpan.append(i)
    return df.iloc[simpan].reset_index(drop=True)


# ------------------------------------------------------------ matriks jarak
def proyeksi_meter(lon, lat, lon0, lat0):
    """Proyeksi sederhana (equirectangular) ke meter, cukup akurat untuk satu kota."""
    x = (np.asarray(lon, dtype=float) - lon0) * 111_320 * np.cos(np.radians(lat0))
    y = (np.asarray(lat, dtype=float) - lat0) * 110_574
    return x, y


def simpul_terdekat(G, lon, lat):
    """Simpul jalan terdekat untuk tiap titik. Kembalikan (id_simpul, jarak_snap_m)."""
    ids = np.array(list(G.nodes))
    nx_ = np.array([G.nodes[i]["x"] for i in ids], dtype=float)
    ny_ = np.array([G.nodes[i]["y"] for i in ids], dtype=float)
    lon0, lat0 = nx_.mean(), ny_.mean()
    gx, gy = proyeksi_meter(nx_, ny_, lon0, lat0)
    px, py = proyeksi_meter(lon, lat, lon0, lat0)
    hasil, jarak = [], []
    for a, b in zip(px, py):
        d2 = (gx - a) ** 2 + (gy - b) ** 2
        k = int(np.argmin(d2))
        hasil.append(ids[k])
        jarak.append(float(np.sqrt(d2[k])))
    return np.array(hasil), np.array(jarak)


def bangun_matriks(G, lon, lat):
    """Matriks jarak jalan (km) D[i, j] = jarak i -> j (asimetris karena jalan satu arah)."""
    simpul, jarak_snap = simpul_terdekat(G, lon, lat)
    panjang = {}
    for s in dict.fromkeys(simpul.tolist()):
        panjang[s] = nx.single_source_dijkstra_path_length(G, s, weight="length")
    n = len(simpul)
    D = np.zeros((n, n))
    for i, si in enumerate(simpul.tolist()):
        pl = panjang[si]
        for j, sj in enumerate(simpul.tolist()):
            D[i, j] = pl.get(sj, np.inf) / 1000.0
    return D, simpul, jarak_snap
