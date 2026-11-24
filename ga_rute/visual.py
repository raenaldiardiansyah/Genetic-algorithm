"""Fungsi bantu visualisasi rute di jaringan jalan (osmnx/networkx + matplotlib)."""
import numpy as np
import networkx as nx


def jalur_rute(G, simpul, urutan, cache=None):
    """Koordinat (x, y) rute melalui jalan: gudang -> urutan toko -> gudang.

    simpul: id simpul jalan untuk [gudang, T1..TN] (indeks 0 = gudang).
    urutan: rute berisi indeks toko 1..N. cache: kamus untuk menyimpan jalur terpendek antar-simpul.
    """
    cache = {} if cache is None else cache
    urut = [0] + [int(t) for t in urutan] + [0]
    xs, ys = [], []
    for a, b in zip(urut[:-1], urut[1:]):
        u, v = simpul[a], simpul[b]
        if (u, v) not in cache:
            cache[(u, v)] = [u] if u == v else nx.shortest_path(G, u, v, weight="length")
        for n in cache[(u, v)]:
            xs.append(G.nodes[n]["x"])
            ys.append(G.nodes[n]["y"])
    return np.array(xs), np.array(ys)


def pilih_bingkai(generasi, maks_bingkai=30):
    """Daftar generasi untuk GIF: rapat di awal (perubahan cepat), jarang di akhir."""
    kandidat = np.unique(np.round(np.geomspace(1, generasi, maks_bingkai)).astype(int)) - 1
    return sorted(set(kandidat.tolist()) | {0, generasi - 1})
