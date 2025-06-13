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

        output = BytesIO()
        df_output.to_excel(output, index=False)
        st.download_button("⬇️ Download Hasil Excel", data=output.getvalue(), file_name="hasil_dashboard.xlsx")

        st.subheader("Pie Chart Kepatuhan WP")
        pie_data = df_output["Klasifikasi Kepatuhan"].value_counts().reset_index()
        pie_data.columns = ["Klasifikasi", "Jumlah"]
        fig_pie = px.pie(
            pie_data,
            names="Klasifikasi",
            values="Jumlah",
            title="Distribusi Kepatuhan WP",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📈 Tren Pembayaran Pajak per Bulan")
        if payment_cols:
            bulanan = df_output[payment_cols].sum().reset_index()
            bulanan.columns = ["Bulan", "Total Pembayaran"]
            bulanan["Bulan"] = pd.to_datetime(bulanan["Bulan"])
            bulanan = bulanan.sort_values("Bulan")

            fig_line = px.line(
                bulanan,
                x="Bulan",
                y="Total Pembayaran",
                title="Total Pembayaran Pajak per Bulan",
                markers=True,
                line_shape="spline",
                color_discrete_sequence=["#FFB6C1"]
            )
            st.plotly_chart(fig_line, use_container_width=True)

            st.subheader("🏅 Top 5 Objek Pajak Berdasarkan Total Pembayaran (Tabel Lengkap)")
            
            # Ambil kolom yang dibutuhkan
            top_wp_detail = (
                df_output[["Nama Op", "Total Pembayaran", "Nm Unit", "KLASIFIKASI"]]
                .groupby(["Nama Op", "Nm Unit", "KLASIFIKASI"], as_index=False)
                .sum()
                .sort_values("Total Pembayaran", ascending=False)
                .head(5)
            )
            
            # Tampilkan sebagai tabel
            st.dataframe(top_wp_detail.style.format({"Total Pembayaran": "Rp{:,.0f}"}), use_container_width=True)

