# Dokumentasi Proyek: Optimasi Rute Distribusi ke Gerai Indomaret di Kota Bandung dengan Algoritma Genetika

Tugas Besar Kecerdasan Buatan 2026–2027 · Dosen: Dr. Budhi Irawan, S.Si., M.T. · Universitas Telkom
Kelompok [10]: [Muhammad Nibroos Labiib] · [Muhammad Rafi Al Fauzan] · [Raemaldi Ardiansyah Sidik]

> Dokumen ini merangkum seluruh pekerjaan yang sudah dilakukan: rancangan, data, kode, hasil, keterbatasan, dan langkah yang tersisa. Semua angka hasil diambil dari keluaran program yang dijalankan pada data Kota Bandung (OpenStreetMap), kecuali yang diberi tanda **[perlu diperiksa]**.

---

## 1. Ringkasan

**Masalah.** Satu truk berangkat dari gudang, mengunjungi N gerai tepat satu kali, lalu kembali ke gudang. Tujuannya meminimalkan total jarak jalan. Karena ada jalan satu arah, jarak A→B bisa berbeda dari B→A, sehingga masalahnya adalah **ATSP** (Asymmetric Traveling Salesman Problem) satu kendaraan.

**Pendekatan.** Dijkstra menghitung jarak jalan antar-titik di jaringan jalan asli OpenStreetMap. Algoritma Genetika (ditulis sendiri dengan numpy, tanpa pustaka GA) mencari urutan kunjungan.

**Hasil utama.**

- GA lebih baik dari *nearest neighbor* (NN) di seluruh 18 kombinasi merek × gudang × ukuran. Rute GA lebih pendek sekitar 9,6% sampai 14,1% (median).
- Pada 10 toko, GA menemukan rute optimal (dibandingkan Held-Karp) di 97% sampai 100% skenario.
- Pada 20 toko, median gap ke OR-Tools sekitar 0% sampai 2,2%. Pada 30 toko, median gap 2,7% sampai 8,1% dan gap terburuk sampai 24,5%. **GA murni belum mendekati optimal pada 30 toko.**
- Pada soal TSPLIB yang lebih besar (71 sampai 100 simpul) GA murni jauh dari optimum (gap rata-rata 12,6% sampai 79,7%). Hasil ini dilaporkan apa adanya.

---

## 2. Status pekerjaan

| Bagian | Status |
|---|---|
| Pengambilan data OSM, matriks jarak Dijkstra | Selesai |
| GA (OX, inversi, turnamen, elitisme, penjaga keragaman) | Selesai, 20 tes lulus |
| Pembanding: NN, Held-Karp, OR-Tools, GA + 2-opt | Selesai |
| Eksperimen utama (900 skenario per merek) | Selesai |
| Eksperimen parameter (Indomaret, 30 toko) | Selesai |
| Validasi TSPLIB (kroA100, ftv33, ftv70) | Selesai |
| Visualisasi: grafik konvergensi, peta rute, GIF per generasi | **Belum dibuat** |
| Pembaruan slide dengan angka sebenarnya | **Belum** (lihat bagian 10) |
| Laporan, video YouTube (publik), repositori GitHub | **Belum** |

---

## 3. Struktur proyek

```
tubes-ga-bandung/
├── ga_rute/
│   ├── ga.py            GA: populasi, turnamen, rank, OX, PMX, inversi, elitisme, 2-opt
│   ├── baselines.py     Nearest neighbor, Held-Karp, OR-Tools
│   ├── data.py          Unduh OSM, snap ke simpul jalan, matriks Dijkstra
│   ├── skenario.py      Zona toko, pembuatan skenario (seed tetap), submatriks
│   ├── tsplib.py        Pembaca file TSPLIB (.tsp EUC_2D, .atsp FULL_MATRIX)
│   └── konfig.py        Radius, ukuran, jumlah skenario, populasi, generasi
├── scripts/
│   ├── demo_sintetis.py          Demo GA pada data sintetis (tanpa OSM)
│   ├── 01_unduh_osm.py           Unduh batas kota, toko, dan jalan dari OSM
│   ├── 02_bangun_matriks.py      Matriks jarak jalan + pengecekan zona
│   ├── 03_cek_radius.py          Tabel jumlah toko per radius (lihat Lampiran A)
│   ├── 04_benchmark.py           Ukur waktu satu run GA (Lampiran A)
│   ├── 05_runner.py              Eksperimen utama (paralel, bisa dilanjutkan)
│   ├── 06_ringkasan.py           Statistik dan tabel ringkasan
│   ├── 07_cek_ga_kalah.py        Skenario saat GA lebih panjang dari NN (Lampiran A)
│   ├── 08_ortools.py             Patokan OR-Tools (20 dan 30 toko)
│   ├── 09_eksperimen_parameter.py  Penyetelan parameter pada skenario terpisah
│   └── 10_tsplib.py              Validasi pada soal TSPLIB
├── tests/               20 tes otomatis (pytest)
├── data/                gudang.csv, indomaret.csv, alfamart.csv, jalan_bandung.graphml,
│                        matriks_*.npy, tsplib/
├── hasil/               CSV hasil eksperimen dan ringkasan
└── requirements.txt
```

---

## 4. Lingkungan dan cara menjalankan

**Sistem yang dipakai:** Windows, VS Code, Python **3.12** (`.venv312`). OR-Tools belum tersedia untuk Python 3.15, jadi gunakan 3.12.

```
py -3.12 -m venv .venv312
.venv312\Scripts\Activate.ps1
pip install --default-timeout=100 --retries 10 -r requirements.txt
pytest                                  # 20 passed
```

**Urutan eksperimen dari nol:**

```
python scripts/01_unduh_osm.py          # sekali saja, bisa puluhan menit (butuh internet)
python scripts/02_bangun_matriks.py     # matriks jarak + cek jumlah toko per zona
python scripts/05_runner.py --merek semua                 # GA, NN, Held-Karp (10 toko)
python scripts/05_runner.py --merek semua --lokal akhir   # GA + 2-opt di akhir
python scripts/08_ortools.py --merek semua --detik 2      # patokan OR-Tools (20, 30 toko)
python scripts/06_ringkasan.py                            # tabel ringkasan
python scripts/09_eksperimen_parameter.py --merek indomaret --n 30
python scripts/10_tsplib.py                               # taruh file TSPLIB di data/tsplib/
python scripts/10_tsplib.py --lokal akhir
```

Runner dan OR-Tools menulis hasil per skenario, sehingga bisa dihentikan (Ctrl+C) dan dilanjutkan dengan perintah yang sama. Pada komputer Anda satu kali GA (100 individu × 1.000 generasi) sekitar 2,7 sampai 3,7 detik.

---

## 5. Data

### 5.1 Sumber
| Data | Sumber | Keterangan |
|---|---|---|
| Gerai Indomaret | OpenStreetMap | **172 gerai** |
| Gerai Alfamart | OpenStreetMap | **144 gerai** (replikasi) |
| Jaringan jalan | OpenStreetMap (osmnx, `network_type="drive"`) | Batas Kota Bandung + buffer 2 km, komponen terhubung kuat terbesar |
| Soal validasi | TSPLIB (Reinelt, 1991) | kroA100, ftv33, ftv70 |

Jumlah gerai berasal dari ukuran matriks jarak (175 dan 147 titik, masing-masing dikurangi 3 gudang). Slide awal menyebut 173 dan 148; angka dari program yang benar. Slide menyebut snapshot 17 Nov 2026, padahal data diunduh sekitar 21 Nov 2026. **[perlu diperiksa]**: catat tanggal unduh yang sebenarnya.

Lisensi data OSM: ODbL, atribusi "© OpenStreetMap contributors".

### 5.2 Pemrosesan gerai
1. Ambil semua fitur OSM dengan `shop=convenience` atau `shop=supermarket` di dalam batas Kota Bandung.
2. Saring berdasarkan nama, merek, atau operator yang memuat "indomaret" atau "alfamart" (huruf besar/kecil diabaikan).
3. Gerai yang terdaftar dua kali (misalnya titik dan bangunan) dalam jarak < 25 m digabung.
4. Setiap gerai di-*snap* ke simpul jalan terdekat. Jarak snap median sekitar 31 sampai 34 m, maksimum 298 m (Indomaret) dan 207 m (Alfamart).

### 5.3 Matriks jarak
Dijkstra (networkx, bobot `length`) dari tiap simpul ke seluruh simpul lain. Matriks berukuran 175×175 (Indomaret) dan 147×147 (Alfamart), tiga baris pertama adalah gudang. Seluruh nilai terhingga. Selisih terbesar jarak A→B terhadap B→A: 3,40 km (Indomaret) dan 3,47 km (Alfamart), bukti bahwa jalan satu arah terbaca.

### 5.4 Gudang (simulasi)
Tiga titik, dipakai bersama oleh kedua merek agar perbandingan adil. **Bukan lokasi pusat distribusi asli perusahaan.**

| No | Nama | Lintang | Bujur |
|---|---|---|---|
| 1 | Gudang Timur (area Gedebage) | -6.9355 | 107.6855 |
| 2 | Gudang Barat (area Kopo) | -6.9478 | 107.5861 |
| 3 | Gudang Utara (area Setiabudi) | -6.8781 | 107.6033 |

**[perlu diisi]**: alasan pemilihan tiap lokasi (permintaan slide 15: "alasan tertulis").

### 5.5 Zona dan skenario
- **Zona:** gerai dengan jarak jalan ≤ **8 km** dari gudang (diambil nilai terkecil dari kedua arah). Radius dipilih dari tabel jumlah toko per radius (target ≥ 45 toko per sel). Pada 6 km, sebagian sel hanya berisi 36 toko, terlalu sedikit untuk skenario 30 toko.

| | Gudang 1 | Gudang 2 | Gudang 3 |
|---|---|---|---|
| Indomaret dalam 8 km | 67 | 67 | 103 |
| Alfamart dalam 8 km | 61 | 72 | 85 |

- **Skenario:** N toko (10, 20, atau 30) dipilih acak tanpa pengembalian dari zona. Seed = `no_gudang × 100000 + N × 1000 + k`, dengan k = 1..100 (evaluasi) dan k = 101..120 (penyetelan parameter, gudang bergilir). Total: 3 ukuran × 3 gudang × 100 skenario = **900 per merek**.

---

## 6. Algoritma Genetika

| Komponen | Pengaturan |
|---|---|
| Kromosom | Permutasi toko 1..N (gudang tidak dikodekan) |
| Fungsi biaya | Panjang rute = d(G,t₁) + Σ d(tₖ,tₖ₊₁) + d(t_N,G), asimetris |
| Populasi | 100 individu acak |
| Generasi | 1.000 (anggaran 100.000 evaluasi) |
| Seleksi | Turnamen k = 3 (pembanding: rank-based, tekanan 1,5) |
| Crossover | Order Crossover (OX), peluang 0,9; anak = induk 1 bila tidak di-crossover (pembanding: PMX) |
| Mutasi | Inversi satu potongan, **peluang 0,2 per individu** |
| Elitisme | 2 individu terbaik lolos langsung |
| Penjaga keragaman | Anak kembar dari individu yang sudah ada dimutasi (maks. 10 percobaan) sampai unik |
| Varian | GA + 2-opt pada hasil akhir (`lokal="akhir"`) |

Implementasi: seleksi, OX, dan mutasi dikerjakan sekaligus untuk seluruh populasi dengan operasi numpy (sekitar 8 kali lebih cepat daripada versi loop Python, hasil identik dengan OX per-individu; ada tes yang membandingkannya).

**Temuan penting selama pengembangan.** Dengan mutasi 0,02 per individu dan tanpa penjaga keragaman, populasi 100 individu menyusut menjadi satu individu dalam sekitar 25 generasi dan GA tidak pernah mencapai optimum. Dengan mutasi 0,2 dan penjaga keragaman, pada uji sintetis 10 toko GA mencapai optimum Held-Karp di 8 dari 8 uji. Tes `test_diversitas_dijaga_agar_tidak_macet` merekam perilaku ini.

---

## 7. Pembanding

| Pembanding | Dipakai untuk | Catatan |
|---|---|---|
| Nearest neighbor | Semua ukuran | Selalu ke gerai terdekat berikutnya |
| Held-Karp | 10 toko | Optimum pasti (dynamic programming) |
| OR-Tools | 20 dan 30 toko | Guided Local Search, strategi awal PATH_CHEAPEST_ARC, jarak dibulatkan ke meter. Dibatasi waktu per skenario (lihat kolom `detik` pada `hasil/ortools_*.csv`), jadi **bukan optimum pasti** |
| GA + 2-opt | Semua ukuran | 2-opt khusus jarak asimetris, hanya pada hasil akhir |

Statistik: uji Wilcoxon berpasangan, koreksi Holm, efek berupa korelasi rank-biserial. GA vs NN diuji satu arah (NN lebih panjang); GA vs OR-Tools diuji dua arah.

---

## 8. Hasil

### 8.1 GA vs nearest neighbor dan Held-Karp (100 skenario per baris)

`hemat` = median penghematan GA terhadap NN. `GA lebih baik` = persen skenario dengan rute GA lebih pendek dari NN (sisanya sama atau lebih panjang). `optimal` = persen skenario 10 toko dengan hasil GA sama dengan Held-Karp.

| Merek | Gudang | N | GA rata² (km) | NN rata² (km) | Hemat (%) | GA lebih baik (%) | Gap HK (%) | Optimal (%) |
|---|---|---|---|---|---|---|---|---|
| Alfamart | 1 | 10 | 33,665 | 38,021 | 10,98 | 96 | 0,000 | 100 |
| Alfamart | 1 | 20 | 47,180 | 53,901 | 11,99 | 100 | | |
| Alfamart | 1 | 30 | 57,175 | 63,697 | 9,60 | 97 | | |
| Alfamart | 2 | 10 | 29,060 | 32,993 | 11,61 | 93 | 0,057 | 98 |
| Alfamart | 2 | 20 | 40,498 | 46,331 | 11,99 | 99 | | |
| Alfamart | 2 | 30 | 51,182 | 56,894 | 10,06 | 96 | | |
| Alfamart | 3 | 10 | 30,584 | 34,494 | 11,43 | 88 | 0,100 | 97 |
| Alfamart | 3 | 20 | 42,661 | 48,622 | 11,27 | 98 | | |
| Alfamart | 3 | 30 | 52,683 | 59,641 | 10,78 | 95 | | |
| Indomaret | 1 | 10 | 34,817 | 39,152 | 10,62 | 96 | 0,000 | 100 |
| Indomaret | 1 | 20 | 47,591 | 55,115 | 13,39 | 100 | | |
| Indomaret | 1 | 30 | 58,305 | 66,702 | 12,56 | 94 | | |
| Indomaret | 2 | 10 | 30,186 | 34,386 | 11,52 | 97 | 0,000 | 100 |
| Indomaret | 2 | 20 | 43,023 | 50,154 | 14,12 | 98 | | |
| Indomaret | 2 | 30 | 54,178 | 61,708 | 12,06 | 93 | | |
| Indomaret | 3 | 10 | 30,954 | 34,966 | 10,20 | 96 | 0,032 | 99 |
| Indomaret | 3 | 20 | 43,425 | 49,723 | 12,07 | 95 | | |
| Indomaret | 3 | 30 | 55,733 | 63,114 | 11,93 | 93 | | |

Seluruh nilai `p` (Holm) < 0,001; efek rank-biserial 0,970 sampai 1,000.

**Kasus GA lebih panjang dari NN:** 44 dari 1.800 skenario (2,4%). Pada 10 toko: 2 kasus (kalah 0,6% sampai 1,4%); 20 toko: 10 kasus (1,3% sampai 3,2%); 30 toko: 32 kasus (median 2,7%, terburuk 10,8%).

### 8.2 GA vs OR-Tools (20 dan 30 toko)

Gap positif berarti rute GA lebih panjang dari OR-Tools.

| Merek | Gudang | N | Median gap GA (%) | Q1 | Q3 | Maks | Median gap NN (%) | GA lebih baik dari OR-Tools (%) |
|---|---|---|---|---|---|---|---|---|
| Alfamart | 1 | 20 | 0,90 | 0,00 | 2,80 | 9,43 | 15,92 | 3 |
| Alfamart | 1 | 30 | 3,13 | 1,31 | 5,45 | 18,41 | 15,34 | 8 |
| Alfamart | 2 | 20 | 2,14 | 0,49 | 4,06 | 11,32 | 16,44 | 2 |
| Alfamart | 2 | 30 | 7,61 | 4,93 | 10,41 | 18,46 | 18,90 | 3 |
| Alfamart | 3 | 20 | 0,68 | 0,00 | 3,09 | 12,82 | 15,35 | 0 |
| Alfamart | 3 | 30 | 5,90 | 2,41 | 9,60 | 24,50 | 20,11 | 2 |
| Indomaret | 1 | 20 | 0,00 | 0,00 | 1,43 | 8,06 | 16,70 | 2 |
| Indomaret | 1 | 30 | 2,68 | 0,65 | 4,85 | 18,21 | 18,45 | 7 |
| Indomaret | 2 | 20 | 2,16 | 0,00 | 5,00 | 13,84 | 20,07 | 1 |
| Indomaret | 2 | 30 | 8,11 | 3,29 | 11,37 | 22,84 | 23,08 | 5 |
| Indomaret | 3 | 20 | 2,07 | 0,10 | 4,06 | 11,68 | 16,74 | 2 |
| Indomaret | 3 | 30 | 5,62 | 3,00 | 8,97 | 20,26 | 19,55 | 4 |

Catatan: pada sebagian skenario GA mengalahkan OR-Tools, artinya patokan OR-Tools dengan batas waktu bukan optimum sejati. Gap yang dilaporkan sedikit meremehkan jarak sebenarnya ke optimum. Gudang 2 konsisten paling sulit pada 30 toko.

### 8.3 GA murni vs GA + 2-opt (300 skenario per baris)

| Merek | N | Perbaikan rata² (%) | Perbaikan maks (%) | GA kalah dari NN | GA+2-opt kalah dari NN |
|---|---|---|---|---|---|
| Alfamart | 10 | 0,000 | 0,000 | 2 | 2 |
| Alfamart | 20 | 0,045 | 2,926 | 3 | 3 |
| Alfamart | 30 | 0,357 | 9,185 | 12 | 9 |
| Indomaret | 10 | 0,000 | 0,000 | 0 | 0 |
| Indomaret | 20 | 0,030 | 5,685 | 7 | 7 |
| Indomaret | 30 | 0,269 | 9,548 | 20 | 18 |

2-opt di akhir hanya memberi perbaikan kecil. Kelemahan GA terletak pada proses pencariannya, bukan penyempurnaan akhir.

### 8.4 Eksperimen parameter (Indomaret, 30 toko, 20 skenario terpisah, rata-rata 3 seed)

Satu faktor diubah dari konfigurasi dasar, anggaran 100.000 evaluasi (populasi 50 → 2.000 generasi; populasi 200 → 500 generasi).

| Konfigurasi | Gap rata² ke OR-Tools (%) | Median (%) | Lebih baik dari dasar (% skenario) | Detik per run |
|---|---|---|---|---|
| GA + 2-opt | 4,21 | 3,29 | 50 | 5,3 |
| **Dasar** (pop 100, mutasi 0,2, OX, turnamen) | **4,47** | 3,90 | – | 3,9 |
| Populasi 50 | 4,59 | 3,65 | 50 | 8,0 |
| PMX | 4,69 | 4,09 | 40 | 23,7 |
| Mutasi 0,02 | 5,10 | 4,95 | 45 | 7,9 |
| Mutasi 0,05 | 5,38 | 5,16 | 40 | 4,7 |
| Mutasi 0,1 | 5,56 | 5,40 | 30 | 4,1 |
| Populasi 200 | 8,20 | 8,46 | 25 | 4,6 |
| Mutasi 0,5 | 9,12 | 8,08 | 5 | 2,9 |
| Rank-based (tekanan 1,5) | 24,08 | 24,76 | 0 | 4,6 |

Empat konfigurasi teratas tidak dapat dibedakan secara meyakinkan (simpangan antar skenario sekitar 3,4 poin, selisih hanya 0,1 sampai 0,3). Konfigurasi dasar dipertahankan. Mutasi berpola U terbalik (0,2 terbaik). PMX 6 kali lebih lambat tanpa manfaat. Seleksi rank-based pada tekanan 1,5 sangat buruk; temuan ini berlaku untuk pengaturan tersebut saja.

### 8.5 Validasi TSPLIB (10 seed, populasi 100, 1.000 generasi)

| Soal | Optimum | GA murni: gap rata² / terbaik | GA + 2-opt: gap rata² / terbaik |
|---|---|---|---|
| ftv33 (34 simpul, asimetris) | 1286 | 12,61% / 4,74% | 12,40% / 4,74% |
| ftv70 (71 simpul, asimetris) | 1950 | 51,43% / 35,90% | 48,01% / 35,90% |
| kroA100 (100 kota, simetris) | 21282 | 79,65% / 61,13% | **5,86% / 2,33%** |

GA tidak mencapai optimum pada satu pun dari 30 run. Kualitas turun cepat bila ukuran masalah naik pada anggaran 100.000 evaluasi. 2-opt sangat membantu pada soal simetris (kroA100), tetapi hampir tidak pada soal asimetris; dugaan: pembalikan potongan pada jarak asimetris mengubah biaya seluruh ruas di dalamnya sehingga jarang menemukan perbaikan, dan Or-opt lebih cocok (belum diuji).

Pemeriksaan file: OR-Tools menemukan 21282 (kroA100) dan 1286 (ftv33) persis, dan 1950 (ftv70) pada batas waktu 120 detik (1967 pada 60 detik, 2033 pada 20 detik). Tidak ada hasil lebih kecil dari nilai optimum resmi. **[perlu diperiksa]**: cocokkan nilai optimum ftv33 dan ftv70 dengan daftar resmi TSPLIB sebelum dilaporkan.

---

## 9. Keterbatasan dan catatan jujur

1. **Data OSM tidak lengkap.** 172 dan 144 adalah jumlah gerai yang tercatat di OSM, bukan jumlah resmi gerai di Bandung.
2. **Gudang dan skenario adalah simulasi.** Lokasi gudang tidak mewakili pusat distribusi asli, dan daftar pesanan harian perusahaan tidak publik.
3. **Skenario dalam satu sel tidak sepenuhnya independen.** Skenario diambil dari zona yang sama (61 sampai 103 gerai), sehingga berbagi gerai. Ini paling terasa pada sel dengan zona kecil.
4. **Hasil GA tidak sama persis (bit demi bit) antar komputer** untuk 20 dan 30 toko. GA sangat peka terhadap selisih hitungan di digit terakhir: perturbasi relatif 10⁻¹³ pada matriks mengubah hasil 30 toko di 5 dari 6 skenario uji, sampai sekitar 2,5%. Hasil NN, Held-Karp, dan GA 10 toko identik di semua komputer. Kesimpulan statistik stabil, angka rinci bergeser tipis. Hasil GA + 2-opt hanya valid dipasangkan dengan GA murni dari komputer yang sama.
5. **Satu run GA per skenario.** Variasi antar run bisa besar pada 30 toko. Penggunaan beberapa seed dan pelaporan sebaran akan lebih kuat.
6. **OR-Tools dibatasi waktu.** Patokan bukan optimum pasti; GA sesekali lebih baik dari OR-Tools.
7. **Kesetaraan model dengan asumsi slide.** Tidak ada kemacetan, jendela waktu, kapasitas truk, atau banyak truk (asumsi A1–A7 di slide); waktu bongkar muat tidak dihitung; jarak dari titik toko ke simpul jalan (snap) diabaikan.
8. **Eksperimen parameter terbatas.** Hanya Indomaret, 30 toko, 20 skenario, satu faktor sekali waktu (interaksi antarfaktor tidak diuji).
9. **GA belum mendekati optimal untuk masalah lebih besar** (30 toko ke atas, TSPLIB 71 dan 100 simpul).

---

## 10. Perbedaan dengan slide yang perlu diperbarui

| Slide | Isi lama | Isi yang benar |
|---|---|---|
| 4, 9, 14, 15 | 173 Indomaret, 148 Alfamart | 172 Indomaret, 144 Alfamart (tanggal unduh sebenarnya) |
| 14 | Zona ≤ 6 km | Zona ≤ 8 km jarak jalan |
| 4 | "Tiap jaringan punya gudang sendiri" | Gudang simulasi yang sama untuk kedua merek (agar perbandingan adil), bukan gudang asli |
| 11–13 | Mutasi dijelaskan umum | Mutasi inversi per individu, peluang 0,2, dengan penjaga keragaman |
| 18 | Mutasi {0,02; 0,05; 0,1; 0,2; 0,5} | Sudah sesuai; hasil: 0,2 terbaik (hanya diuji lengkap pada Indomaret 30 toko) |
| 18 | "Membuktikan GA bekerja" | Sebut sebagai pengukuran gap, dengan hasil TSPLIB yang jauh dari optimum untuk GA murni |
| 17 | Peta rute dan GIF | Belum ada; perlu skrip visualisasi |
| 19 | Jadwal 26 Des | Eksperimen selesai lebih awal; sisa laporan, video, GitHub |

---

## 11. Langkah yang tersisa

- [ ] Skrip visualisasi: grafik konvergensi, peta rute di jaringan jalan asli (osmnx), GIF per generasi
- [ ] Isi alasan pemilihan tiga gudang (bagian 5.4)
- [ ] Perbarui slide sesuai bagian 10
- [ ] Cocokkan nilai optimum ftv33 dan ftv70 dengan daftar resmi TSPLIB
- [ ] (Opsional) Beberapa seed per skenario; Or-opt untuk soal asimetris; penyetelan pada Alfamart dan 20 toko
- [ ] Tulis laporan (rancangan, hasil, keterbatasan)
- [ ] Rekam video dan unggah ke YouTube (publik)
- [ ] Unggah ke GitHub (kode, `data/`, `hasil/`, README), cantumkan atribusi OSM dan TSPLIB
- [ ] Isi nama kelompok dan pembagian tugas
- [ ] Konfirmasi ke dosen: makna "minimal 100 sampel" (100 lokasi data atau 100 skenario)

---

## 12. Sumber dan atribusi

- OpenStreetMap contributors, lisensi ODbL.
- G. Reinelt, *TSPLIB: A Traveling Salesman Problem Library*, ORSA Journal on Computing 3(4), 1991, hlm. 376–384. File kroA100, ftv33, ftv70 diperoleh dari salinan di GitHub karena situs TSPLIB95 tidak dapat diakses; isinya diperiksa konsisten (bagian 8.5).
- Google OR-Tools (solver rute) · osmnx · networkx · numpy · pandas · scipy · matplotlib · pytest.
- Held, M. dan Karp, R. M., 1962 (dynamic programming untuk TSP).
- Davis, 1985 (Order Crossover); Goldberg dan Lingle, 1985 (PMX). **[perlu diperiksa]**: lengkapi rujukan sebelum dimasukkan ke laporan.

---

## Lampiran A. Skrip bantu

**`scripts/03_cek_radius.py`**

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
from ga_rute.skenario import toko_dalam_zona

gudang = pd.read_csv("data/gudang.csv")
for merek in ("indomaret", "alfamart"):
    D = np.load(f"data/matriks_{merek}.npy")
    idx = list(range(len(gudang), D.shape[0]))
    print(f"\n{merek}: jumlah toko dalam zona")
    print("radius_km | " + " | ".join(f"gudang {i+1}" for i in range(len(gudang))))
    for r in (6, 8, 10, 12, 14, 16, 20):
        jml = [len(toko_dalam_zona(D, k, idx, r)) for k in range(len(gudang))]
        print(f"{r:>9} | " + " | ".join(f"{j:>8}" for j in jml))
```

**`scripts/04_benchmark.py`** (radius 10 km dipakai di sini hanya untuk mengukur waktu)

```python
import sys, pathlib, time, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
from ga_rute.ga import jalankan_ga
from ga_rute.skenario import (toko_dalam_zona, buat_skenario,
                              submatriks, seed_skenario)

print("Jumlah core CPU:", os.cpu_count())
D = np.load("data/matriks_indomaret.npy")
idx = list(range(3, D.shape[0]))
zona = toko_dalam_zona(D, 0, idx, 10)
for n in (10, 20, 30):
    toko = buat_skenario(zona, n, seed_skenario(1, n, 1))
    t = time.time()
    _, hasil, _ = jalankan_ga(submatriks(D, 0, toko), 100, 1000, seed=1)
    print(n, "toko:", round(hasil, 2), "km,", round(time.time() - t, 1), "detik")
```

**`scripts/07_cek_ga_kalah.py`**

```python
import pandas as pd
df = pd.concat([pd.read_csv("hasil/hasil_indomaret.csv"),
                pd.read_csv("hasil/hasil_alfamart.csv")])
kalah = df[df.ga_km > df.nn_km + 1e-9].copy()
kalah["selisih_pct"] = 100 * (kalah.ga_km - kalah.nn_km) / kalah.nn_km
print(len(kalah), "dari", len(df), "skenario: GA lebih panjang dari NN")
print(kalah.groupby("n").selisih_pct.describe().round(2))
```

## Lampiran B. Format file hasil

- `hasil/hasil_<merek>.csv` (dan `_2opt.csv`): `merek, gudang, n, skenario, seed, ga_km, nn_km, hk_km, waktu_ga_s, rute_ga`. Kolom `rute_ga` berisi nomor baris gerai (mulai 0) pada `data/<merek>.csv` menurut urutan kunjungan.
- `hasil/ortools_<merek>.csv`: `merek, gudang, n, skenario, seed, or_km, detik`.
- `hasil/parameter_<merek>_n<N>.csv`: `konfig, skenario, gudang, seed_ke, km, detik` (OR-Tools bertanda `konfig = OR-Tools`).
- `hasil/ringkasan*.csv`: tabel ringkasan dari `06_ringkasan.py` dan `09_eksperimen_parameter.py`.
