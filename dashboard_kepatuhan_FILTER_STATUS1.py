import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard Kepatuhan Pajak", layout="wide")

st.title("📊 Dashboard Kepatuhan Pajak")

st.markdown("Silakan upload file Excel berisi data setoran masa pajak.")

uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_options = xls.sheet_names
    selected_sheet = st.selectbox("Pilih Sheet", sheet_options)

    if selected_sheet:
        df_input = pd.read_excel(xls, sheet_name=selected_sheet)

        # ✅ Hapus kolom duplikat
        df_input = df_input.loc[:, ~df_input.columns.duplicated()]

        # ✅ Normalisasi nama kolom
        df_input.columns = df_input.columns.str.strip().str.lower().str.replace(" ", "").str.replace(".", "")

        # ✅ Nama alias kolom penting
        alias_nama_op = ['namaop', 'namawp']
        alias_unit = ['upppd', 'unit', 'nmunit']
        alias_kategori = ['kategori', 'klasifikasi', 'jenishiburan']
        alias_status = ['status']
        alias_tmt = ['tmt', 'tm']
        alias_bulan = ['jan', 'feb', 'mar', 'apr', 'mei', 'jun', 'jul', 'agu', 'sep', 'okt', 'nov', 'des']

        def cari_kolom(possibles):
            for col in possibles:
                if col in df_input.columns:
                    return col
            return None

        # ✅ Mapping kolom
        kol_nama_op = cari_kolom(alias_nama_op)
        kol_unit = cari_kolom(alias_unit)
        kol_kategori = cari_kolom(alias_kategori)
        kol_status = cari_kolom(alias_status)
        kol_tmt = cari_kolom(alias_tmt)

        df = df_input.copy()

        # ✅ Rename kolom
        df = df.rename(columns={
            kol_nama_op: 'Nama OP',
            kol_unit: 'UPPPD',
            kol_status: 'STATUS',
            kol_tmt: 'TMT'
        })
        if kol_kategori:
            df = df.rename(columns={kol_kategori: 'KATEGORI'})

        # ✅ Format TMT
        df['TMT'] = pd.to_datetime(df['TMT'], errors='coerce')

        # ✅ Pilih tahun pajak
        tahun_pilihan = st.selectbox("Pilih Tahun Pajak", sorted(df['TMT'].dt.year.dropna().unique(), reverse=True))
        df = df[df['TMT'].dt.year <= tahun_pilihan]

        # ✅ Hitung bulan aktif
        df['Bulan Aktif'] = df['TMT'].apply(lambda x: 12 - x.month + 1 if pd.notnull(x) else 0)

        # ✅ Ambil kolom bulan
        kolom_bulan = [b for b in alias_bulan if b in df.columns]
        df['Bulan Bayar'] = df[kolom_bulan].apply(lambda row: row.notna().sum(), axis=1)
        df['Total Pembayaran'] = df[kolom_bulan].sum(axis=1)

        # ✅ Kepatuhan
        df['Kepatuhan (%)'] = (df['Bulan Bayar'] / df['Bulan Aktif'].replace(0, np.nan)) * 100
        df['Kepatuhan (%)'] = df['Kepatuhan (%)'].fillna(0).round(2)

        def klasifikasi(row):
            selisih = row['Bulan Aktif'] - row['Bulan Bayar']
            if selisih > 3:
                return "TIDAK PATUH"
            elif selisih > 0:
                return "KURANG PATUH"
            return "PATUH"

        df['KLASIFIKASI'] = df.apply(klasifikasi, axis=1)

        # ✅ Format uang
        df['Total Pembayaran'] = df['Total Pembayaran'].apply(lambda x: f"{x:,.2f}")

        # ✅ Tampilkan data
        st.success("✅ Data berhasil diproses dan difilter!")
        st.dataframe(df[['Nama OP', 'UPPPD', 'STATUS', 'TMT', 'Bulan Aktif', 'Bulan Bayar', 'Total Pembayaran', 'Kepatuhan (%)', 'KLASIFIKASI']].head(50), use_container_width=True)

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Ubah Total Pembayaran kembali ke float untuk grafik
df['Total Pembayaran (float)'] = df['Total Pembayaran'].replace(',', '', regex=True).astype(float)

# ===============================
# 📊 PIE CHART: Klasifikasi Kepatuhan
# ===============================
st.subheader("📘 Distribusi Klasifikasi Kepatuhan WP")

pie_data = df['KLASIFIKASI'].value_counts().reset_index()
pie_data.columns = ['Klasifikasi', 'Jumlah']

fig_pie = px.pie(
    pie_data,
    names='Klasifikasi',
    values='Jumlah',
    title='Proporsi Wajib Pajak per Klasifikasi Kepatuhan',
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig_pie, use_container_width=True)

# ===============================
# 📈 LINE CHART: Tren Pembayaran Bulanan
# ===============================
st.subheader(f"📈 Tren Pembayaran Jan–Des {tahun_pilihan}")

# Ambil hanya kolom bulan
bulan_label = {
    'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
    'mei': 'Mei', 'jun': 'Jun', 'jul': 'Jul', 'agu': 'Agu',
    'sep': 'Sep', 'okt': 'Okt', 'nov': 'Nov', 'des': 'Des'
}
bulanan = df[kolom_bulan].copy()
bulanan.columns = [bulan_label.get(col, col) for col in bulanan.columns]

trends = bulanan.sum().reset_index()
trends.columns = ['Bulan', 'Total Pembayaran']

fig_line = px.line(
    trends,
    x='Bulan',
    y='Total Pembayaran',
    markers=True,
    title="Total Pembayaran per Bulan"
)
st.plotly_chart(fig_line, use_container_width=True)

# ===============================
# 🏆 TOP 5 OP dengan Pembayaran Tertinggi
# ===============================
st.subheader("🏆 Top 5 OP berdasarkan Total Pembayaran")

top5 = df.sort_values(by='Total Pembayaran (float)', ascending=False).head(5)
top5_show = top5[['Nama OP', 'UPPPD', 'Total Pembayaran', 'Kepatuhan (%)', 'KLASIFIKASI']]
st.table(top5_show.reset_index(drop=True))

# ===============================
# 📊 Bar Chart Jumlah WP per Klasifikasi
# ===============================
st.subheader("📌 Jumlah Wajib Pajak per Kategori Kepatuhan")

bar_data = df['KLASIFIKASI'].value_counts().reset_index()
bar_data.columns = ['KLASIFIKASI', 'Jumlah WP']

fig_bar = px.bar(
    bar_data,
    x='KLASIFIKASI',
    y='Jumlah WP',
    color='KLASIFIKASI',
    title='Jumlah WP per Kategori Kepatuhan',
    text='Jumlah WP',
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig_bar, use_container_width=True)
