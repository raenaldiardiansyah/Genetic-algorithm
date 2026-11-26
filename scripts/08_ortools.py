"""Langkah 5: patokan OR-Tools untuk skenario 20 dan 30 toko (skenario SAMA dengan 05_runner).
Hasil ke hasil/ortools_<merek>.csv; bisa dilanjutkan bila terhenti.
Perlu Python 3.12+ dan paket ortools.

    python scripts/08_ortools.py --merek indomaret --jumlah 2 --detik 2   # uji cepat
    python scripts/08_ortools.py --merek semua                            # penuh
"""
import sys, os, pathlib, argparse
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)

from ga_rute import konfig
from ga_rute.baselines import ortools_atsp
from ga_rute.skenario import skenario_ke
from ga_rute.runner import muat_matriks, sudah_selesai, jalankan_dan_tulis

KOLOM = ["merek", "gudang", "n", "skenario", "seed", "or_km", "detik"]
DETIK = 5


def kerjakan(tugas):
    merek, g, n, k, detik = tugas
    Ds, _, seed = skenario_ke(muat_matriks(merek), g, n, k)
    _, km = ortools_atsp(Ds, detik=detik)
    return dict(merek=merek, gudang=g + 1, n=n, skenario=k, seed=seed,
                or_km=round(km, 4), detik=detik)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merek", default="semua", choices=["indomaret", "alfamart", "semua"])
    ap.add_argument("--jumlah", type=int, default=konfig.JUMLAH_SKENARIO)
    ap.add_argument("--detik", type=int, default=DETIK, help="batas waktu OR-Tools per skenario")
    ap.add_argument("--proses", type=int, default=os.cpu_count())
    a = ap.parse_args()
    merek_list = ["indomaret", "alfamart"] if a.merek == "semua" else [a.merek]
    for merek in merek_list:
        path = pathlib.Path(f"hasil/ortools_{merek}.csv")
        selesai = sudah_selesai(path)
        tugas = [(merek, g, n, k, a.detik)
                 for g in range(konfig.JUMLAH_GUDANG)
                 for n in konfig.UKURAN if n >= 20
                 for k in range(1, a.jumlah + 1)
                 if (merek, g + 1, n, k) not in selesai]
        total = len(tugas)
        print(f"\n[{merek}] {len(selesai)} sudah selesai, {total} tersisa, "
              f"{a.proses} proses, {a.detik} detik/skenario")
        if not total:
            continue
        jalankan_dan_tulis(path, tugas, kerjakan, KOLOM, a.proses)
    print("\nSelesai.")


if __name__ == "__main__":
    main()
