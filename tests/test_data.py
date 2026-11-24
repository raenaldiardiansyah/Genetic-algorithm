import numpy as np
import networkx as nx
from ga_rute.data import simpul_terdekat, bangun_matriks, hapus_duplikat
from ga_rute.skenario import (toko_dalam_zona, buat_skenario, submatriks,
                              seed_skenario)
import pandas as pd


def graf_cincin():
    """Tiga simpul satu arah a->b->c->a (tiap sisi 1000 m): jarak b->a = 2 km."""
    G = nx.MultiDiGraph()
    G.add_node(1, x=107.600, y=-6.900)
    G.add_node(2, x=107.610, y=-6.900)
    G.add_node(3, x=107.605, y=-6.910)
    for u, v in [(1, 2), (2, 3), (3, 1)]:
        G.add_edge(u, v, length=1000.0)
    return G


def test_matriks_asimetris_dari_jalan_satu_arah():
    G = graf_cincin()
    lon, lat = [107.600, 107.610, 107.605], [-6.900, -6.900, -6.910]
    D, simpul, snap = bangun_matriks(G, lon, lat)
    assert simpul.tolist() == [1, 2, 3]
    assert np.isclose(D[0, 1], 1.0) and np.isclose(D[1, 0], 2.0)
    assert np.allclose(np.diag(D), 0)
    assert snap.max() < 1


def test_simpul_terdekat_memilih_yang_terdekat():
    G = graf_cincin()
    simpul, snap = simpul_terdekat(G, [107.6099], [-6.9001])
    assert simpul[0] == 2 and snap[0] < 30


def test_hapus_duplikat():
    df = pd.DataFrame({"lon": [107.6000, 107.60005, 107.62], "lat": [-6.9, -6.9, -6.9]})
    assert len(hapus_duplikat(df)) == 2


def test_skenario_dapat_diulang_dan_submatriks_benar():
    D = np.arange(36, dtype=float).reshape(6, 6)
    zona = toko_dalam_zona(D, 0, [1, 2, 3, 4, 5], radius_km=100)
    s1 = buat_skenario(zona, 3, seed_skenario(1, 10, 7))
    s2 = buat_skenario(zona, 3, seed_skenario(1, 10, 7))
    assert s1.tolist() == s2.tolist()
    sub = submatriks(D, 0, s1)
    assert sub.shape == (4, 4)
    assert sub[0, 1] == D[0, s1[0]] and sub[1, 0] == D[s1[0], 0]
