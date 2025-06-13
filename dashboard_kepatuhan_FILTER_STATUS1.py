import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="🎨 Dashboard Kepatuhan Pajak Daerah", layout="wide")
st.title("🎯 Dashboard Kepatuhan Pajak Daerah")
st.markdown("Upload file Excel, pilih sheet, filter, dan lihat visualisasinya ✨")

uploaded_file = st.file_uploader("📁 Upload File Excel", type=["xlsx"])
tahun_pajak = st.number_input("📅 Pilih Tahun Pajak", min_value=2000, max_value=2100, value=2024)

def hitung_kepatuhan(df, tahun_pajak):
    df['TMT'] = pd.to_datetime(df['TMT'], errors='coerce')
    payment_cols = [col for col in df.columns if isinstance(col, datetime) and col.year == tahun_pajak]

    total_pembayaran = df[payment_cols].sum(axis=1)

    def hitung_bulan_aktif(tmt):
        if pd.isna(tmt): return 0
        if tmt.year < tahun_pajak:
            return 12
        elif tmt.year > tahun_pajak:
            return 0
        else:
            return 12 - tmt.month + 1

    bulan_aktif = df['TMT'].apply(hitung_bulan_aktif)
    bulan_pembayaran = df[payment_cols].gt(0).sum(axis=1)
    rata_rata_pembayaran = total_pembayaran / bulan_pembayaran.replace(0, 1)
    kepatuhan_persen = bulan_pembayaran / bulan_aktif.replace(0, 1) * 100

    def klasifikasi(row):
        if row['bulan_aktif'] == 0 and row['bulan_pembayaran'] == 0:
            return "Belum Aktif"
        elif row['bulan_pembayaran'] == row['bulan_aktif']:
            return "Patuh"
        elif row['bulan_aktif'] - row['bulan_pembayaran'] <= 3:
            return "Kurang Patuh"
        else:
            return "Tidak Patuh"

    df["Total Pembayaran"] = total_pembayaran
    df["bulan_aktif"] = bulan_aktif
    df["bulan_pembayaran"] = bulan_pembayaran
    df["Rata-rata Pembayaran"] = rata_rata_pembayaran
    df["Kepatuhan (%)"] = kepatuhan_persen
    df["Klasifikasi Kepatuhan"] = df.apply(klasifikasi, axis=1)

    return df, payment_cols

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    selected_sheet = st.selectbox("📄 Pilih Nama Sheet", sheet_names)
    df_input = pd.read_excel(xls, sheet_name=selected_sheet)

    # ✅ Normalisasi nama kolom
    df_input.columns = df_input.columns.str.s
