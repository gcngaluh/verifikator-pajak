import streamlit as st

# 1. LOGIKA INTI (Tax Engine)
class TaxEngine:
    def __init__(self):
        self.ppn_rate = 0.11
        self.batas_pemungutan = 2000000

    def hitung_pajak_dari_bruto(self, gross, kategori, pph_rate, jenis_pph):
        """Menghitung pajak jika diketahui Nilai Kuitansi (Bruto)"""
        
        # Cek apakah nilai Kuitansi (Bruto) di bawah batas pemungutan PPN
        if gross <= self.batas_pemungutan:
            dpp = gross  # Tanpa PPN, maka Bruto otomatis menjadi DPP
            ppn = 0
            
            if kategori == "Barang":
                # Barang di bawah/sama dengan 2jt juga bebas PPh 22
                pph = 0
                jenis_pph_final = "Bebas PPh 22"
            else:
                # Kategori Jasa & lainnya tetap dikenakan PPh walaupun di bawah 2jt
                pph = dpp * pph_rate
                jenis_pph_final = jenis_pph
                
        else:
            # Jika di atas 2 juta, PPN & PPh berlaku normal
            dpp = gross / (1 + self.ppn_rate)
            ppn = dpp * self.ppn_rate
            pph = dpp * pph_rate
            jenis_pph_final = jenis_pph
            
        # Netto = Kuitansi - PPN - PPh
        netto = gross - ppn - pph
        return gross, dpp, ppn, pph, jenis_pph_final, netto

    def hitung_pajak_dari_netto(self, netto, kategori, pph_rate, jenis_pph):
        """Menghitung pajak dan Nilai Kuitansi (Gross-up) jika diketahui Netto"""
        
        # Tahap 1: Estimasi nilai Bruto seandainya TIDAK ada PPN
        if kategori == "Barang":
            gross_estimasi = netto  # Barang <= 2jt bebas PPN & PPh
        else:
            gross_estimasi = netto / (1 - pph_rate) # Jasa <= 2jt bebas PPN, tapi kena PPh
            
        # Tahap 2: Cek apakah estimasi Bruto tersebut masih di bawah batas 2 juta
        if gross_estimasi <= self.batas_pemungutan:
            gross = gross_estimasi
            dpp = gross
            ppn = 0
            
            if kategori == "Barang":
                pph = 0
                jenis_pph_final = "Bebas PPh 22"
            else:
                pph = dpp * pph_rate
                jenis_pph_final = jenis_pph
                
        else:
            # Jika estimasi ternyata menembus 2 juta, gunakan rumus Gross-Up lengkap dengan PPN
            jenis_pph_final = jenis_pph
            gross = netto * (1 + self.ppn_rate) / (1 - pph_rate)
            dpp = gross / (1 + self.ppn_rate)
            ppn = dpp * self.ppn_rate
            pph = dpp * pph_rate
            
        return gross, dpp, ppn, pph, jenis_pph_final, netto


# 2. TAMPILAN WEBSITE (Streamlit)
st.set_page_config(page_title="Verifikator Pajak", page_icon="🛡️", layout="wide")

st.title("🛡️ Verifikator Pajak E-SPJ")
st.write("Otomasi Perhitungan Pajak Kontrak & Kuitansi (Termasuk PPh 4 ayat 2 & Manual)")

# Sidebar untuk navigasi dan input
st.sidebar.header("Mode Perhitungan")
mode = st.sidebar.radio(
    "Pilih skenario yang diketahui:",
    ["Dari Nilai Kuitansi (Bruto)", "Dari Nilai Diterima (Netto)"]
)

st.sidebar.header("Input Data Transaksi")
if mode == "Dari Nilai Kuitansi (Bruto)":
    nilai_input = st.sidebar.number_input("Total Nilai Kuitansi (Rp)", min_value=0, step=1000, value=2500000)
else:
    nilai_input = st.sidebar.number_input("Nilai Diterima Vendor/Netto (Rp)", min_value=0, step=1000, value=2000000)

kat_input = st.sidebar.selectbox("Kategori Belanja", [
    "Barang", 
    "Jasa (PPh 23)",
    "Sewa Tanah dan/atau Bangunan",
    "Pelaksanaan Konstruksi",
    "Konsultansi Konstruksi",
    "Pekerjaan Konstruksi Terintegrasi",
    "Input Manual / Lainnya"
])

# Variabel pembantu default
pph_rate = 0.0
jenis_pph = ""
kategori_engine = "Jasa"
npwp_input = True # Default true untuk pajak final yang tidak terpengaruh NPWP

# Menentukan tarif dan jenis PPh berdasarkan pilihan Kategori
if kat_input == "Barang":
    kategori_engine = "Barang"
    npwp_input = st.sidebar.checkbox("Vendor memiliki NPWP", value=True)
    pph_rate = 0.015 if npwp_input else 0.03
    jenis_pph = "PPh 22"

elif kat_input == "Jasa (PPh 23)":
    kategori_engine = "Jasa"
    npwp_input = st.sidebar.checkbox("Vendor memiliki NPWP", value=True)
    pph_rate = 0.02 if npwp_input else 0.04
    jenis_pph = "PPh 23"

elif kat_input == "Sewa Tanah dan/atau Bangunan":
    kategori_engine = "Sewa"
    pph_rate = 0.10
    jenis_pph = "PPh 4(2) Sewa"
    st.sidebar.info("Tarif Final 10%")

elif kat_input == "Pelaksanaan Konstruksi":
    kategori_engine = "Konstruksi"
    sub_kat = st.sidebar.selectbox("Kualifikasi Penyedia", [
        "Kualifikasi Kecil / Perseorangan (1,75%)",
        "Menengah / Besar / Spesialis (2,65%)",
        "Tidak Memiliki SBU/SKK (4,00%)"
    ])
    if "1,75" in sub_kat: pph_rate = 0.0175
    elif "2,65" in sub_kat: pph_rate = 0.0265
    else: pph_rate = 0.04
    jenis_pph = "PPh 4(2) Pelaksanaan Konst."

elif kat_input == "Konsultansi Konstruksi":
    kategori_engine = "Konstruksi"
    sub_kat = st.sidebar.selectbox("Kualifikasi Penyedia", [
        "Memiliki SBU/SKK (3,50%)",
        "Tidak Memiliki SBU/SKK (6,00%)"
    ])
    if "3,50" in sub_kat: pph_rate = 0.035
    else: pph_rate = 0.06
    jenis_pph = "PPh 4(2) Konsultansi Konst."

elif kat_input == "Pekerjaan Konstruksi Terintegrasi":
    kategori_engine = "Konstruksi"
    sub_kat = st.sidebar.selectbox("Kualifikasi Penyedia", [
        "Memiliki SBU (2,65%)",
        "Tidak Memiliki SBU (4,00%)"
    ])
    if "2,65" in sub_kat: pph_rate = 0.0265
    else: pph_rate = 0.04
    jenis_pph = "PPh 4(2) Konst. Terintegrasi"

elif kat_input == "Input Manual / Lainnya":
    kategori_engine = "Lainnya"
    manual_rate = st.sidebar.number_input("Masukkan Persentase PPh (%)", min_value=0.0, step=0.1, value=2.0)
    pph_rate = manual_rate / 100.0
    jenis_pph = f"PPh ({manual_rate}%)"

submit = st.sidebar.button("Hitung Sekarang")

# Fungsi untuk memformat angka menjadi format Rupiah Indonesia (titik)
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

if submit:
    engine = TaxEngine()
    
    if mode == "Dari Nilai Kuitansi (Bruto)":
        gross, dpp, ppn, pph, jenis_pph_final, netto = engine.hitung_pajak_dari_bruto(
            nilai_input, kategori_engine, pph_rate, jenis_pph
        )
    else:
        gross, dpp, ppn, pph, jenis_pph_final, netto = engine.hitung_pajak_dari_netto(
            nilai_input, kategori_engine, pph_rate, jenis_pph
        )
    
    # Tampilan Hasil di Area Utama
    st.subheader("Hasil Analisis Pajak")
    
    # Menampilkan angka dalam 4 kolom menggunakan st.info agar teks tidak terpotong (...)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"**Nilai Kuitansi (Bruto)**\n### {format_rupiah(gross)}")
    with col2:
        st.info(f"**DPP**\n### {format_rupiah(dpp)}")
    with col3:
        st.info(f"**PPN (11%)**\n### {format_rupiah(ppn)}")
    with col4:
        st.info(f"**{jenis_pph_final}**\n### {format_rupiah(pph)}")
    
    st.divider()
    
    # Menampilkan Highlight Kesimpulan berdasarkan Mode
    if mode == "Dari Nilai Kuitansi (Bruto)":
        st.success(f"### Nilai Bersih Diterima Vendor: {format_rupiah(netto)}")
        st.caption("*(Dihitung dari: Nilai Kuitansi - PPN - PPh)*")
    else:
        st.success(f"### Nilai Kuitansi (Bruto) yang harus ditulis: {format_rupiah(gross)}")
        st.caption("*(Dihitung dengan skema gross-up agar vendor menerima nilai Netto secara utuh)*")
    
    # Penjelasan Aturan
    with st.expander("Lihat Detail Aturan & Catatan"):
        st.write(f"1. Transaksi diklasifikasikan sebagai **{kat_input}** dengan tarif PPh sebesar **{pph_rate*100:g}%**.")
        
        # Peringatan PPN & PPh jika Bruto <= 2 Juta
        if gross <= 2000000:
            if kategori_engine == "Barang":
                st.info("Catatan: Karena nilai bruto ≤ Rp 2.000.000, maka tidak dipungut PPN & PPh 22 sesuai ketentuan bendahara pemerintah.")
            else:
                st.info("Catatan: Karena nilai bruto ≤ Rp 2.000.000, maka tidak dipungut PPN. Namun, PPh atas jasa/sewa tetap dikenakan tanpa batas minimum.")
        
        # Peringatan tidak ada NPWP
        if kat_input == "Barang" and not npwp_input and gross > 2000000:
            st.warning("Peringatan: Tarif PPh 22 dikenakan 100% lebih tinggi karena vendor tidak memiliki NPWP.")
        elif kat_input == "Jasa (PPh 23)" and not npwp_input:
            st.warning("Peringatan: Tarif PPh 23 dikenakan 100% lebih tinggi karena vendor tidak memiliki NPWP.")

# Menambahkan menu Support Developer di posisi bawah
st.divider()
with st.expander("☕ Support Developer"):
    st.markdown("Jika aplikasi ini membantu mempercepat pekerjaan Anda, Anda dapat memberikan dukungan ke developer melalui QRIS di bawah ini:")
    st.image("qris.jpeg", width=350)