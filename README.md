# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Repositori ini berisi analisis data transaksi dari Olist E-Commerce untuk mengevaluasi pertumbuhan jumlah pesanan bulanan sepanjang tahun 2017, mengidentifikasi lima kategori produk dengan volume ulasan negatif tertinggi beserta rasio keterlambatan pengirimannya pada periode Januari–Agustus 2018, serta memetakan segmentasi pelanggan menggunakan metode RFM Analysis.

## Susunan Berkas Proyek
- `dashboard/dashboard.py`: Skrip utama aplikasi dashboard interaktif berbasis Streamlit.
- `dashboard/main_data.csv`: Dataset hasil pembersihan dan penggabungan yang digunakan sebagai sumber data dashboard.
- `data/`: Kumpulan berkas dataset mentah Olist dalam format CSV.
- `notebook.ipynb`: Jupyter Notebook yang memuat seluruh proses analisis mulai dari *Data Wrangling* hingga *Conclusion*.
- `requirements.txt`: Daftar pustaka Python yang diperlukan untuk menjalankan proyek.
- `url.txt`: Berkas teks yang berisi tautan aktif hasil deployment dashboard di Streamlit Community Cloud.

## Cara Menjalankan Dashboard di Komputer Lokal
1. Buka terminal atau command prompt, lalu arahkan ke direktori utama proyek (`submission_I_Komang_Pasek_Adiantara/`).
2. Pasang seluruh pustaka pendukung dengan menjalankan perintah:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi dashboard Streamlit melalui perintah:
   ```bash
   streamlit run dashboard/dashboard.py
   ```
4. Setelah server aktif, antarmuka dashboard akan otomatis terbuka pada peramban (*browser*) di alamat `http://localhost:8501`.