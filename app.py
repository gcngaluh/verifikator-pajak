import streamlit as st

# 1. LOGIKA INTI (Tax Engine)
class TaxEngine:
    def __init__(self):
        self.ppn_rate = 0.11
        self.batas_pemungutan = 2000000

    def hitung_pajak_dari_bruto(self, gross, kategori, pph_rate, jenis_pph):
        """Menghitung pajak jika diketahui Nilai Kuitansi (Bruto)"""
        if gross <= self.batas_pemungutan:
            dpp = gross
            ppn = 0
            if kategori == "Barang":
                pph = 0
                jenis_pph_final = "Bebas PPh 22"
            else:
                pph = dpp * pph_rate
                jenis_pph_final = jenis_pph
        else:
            dpp = gross / (1 + self.ppn_rate)
            ppn = dpp * self.ppn_rate
            pph = dpp * pph_rate
            jenis_pph_final = jenis_pph
            
        netto = gross - ppn - pph
        return gross, dpp, ppn, pph, jenis_pph_final, netto

    def hitung_pajak_dari_netto(self, netto, kategori, pph_rate, jenis_pph):
        """Menghitung pajak dan Nilai Kuitansi (Gross-up) jika diketahui Netto"""
        if kategori == "Barang":
            gross_estimasi = netto 
        else:
            gross_estimasi = netto / (1 - pph_rate) 
            
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

# --- TRIK SESSION STATE UNTUK KOMA OTOMATIS ---
# 1. Mengatur nilai default pertama kali aplikasi dimuat
if "input_nominal" not in st.session_state:
    st.session_state.input_nominal = "2,500,000"

# 2. Fungsi yang dipanggil otomatis saat user selesai mengetik dan menekan Enter
def format_input_koma():
    raw_text = st.session_state.input_nominal
    # Membersihkan semua input (termasuk titik/huruf) sehingga menyisakan murni angkanya saja
    clean_text = ''.join(filter(str.isdigit, str(raw_text)))
    
    # Jika terdeteksi ada angka, format ulang dan selipkan koma ribuan
    if clean_text:
        st.session_state.input_nominal = f"{int(clean_text):,}"
    else:
        st.session_state.input_nominal = "0"

st.sidebar.header("Input Data Transaksi")

# 3. Input dinamis yang terlihat seperti number_input tetapi mendukung auto-format
label_teks = "Total Nilai Kuitansi (Rp)" if mode == "Dari Nilai Kuitansi (Bruto)" else "Nilai Diterima Vendor/Netto (Rp)"

st.sidebar.text_input(
    label=label_teks,
    key="input_nominal",
    on_change=format_input_koma
)

# 4. Ambil teks hasil inputan user, buang komanya di latar belakang agar bisa dihitung mesin
try:
    nilai_input = float(st.session_state.input_nominal.replace(",", ""))
except ValueError:
    nilai_input = 0.0

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
npwp_input = True 

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

submit = st.sidebar.button("Hitung Sekarang", disabled=(nilai_input <= 0))

# Fungsi untuk memformat angka menjadi format Rupiah Indonesia (titik) pada HASIL Output
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
    
    # Menampilkan Highlight Kesimpulan
    if mode == "Dari Nilai Kuitansi (Bruto)":
        st.success(f"### Nilai Bersih Diterima Vendor: {format_rupiah(netto)}")
        st.caption("*(Dihitung dari: Nilai Kuitansi - PPN - PPh)*")
    else:
        st.success(f"### Nilai Kuitansi (Bruto) yang harus ditulis: {format_rupiah(gross)}")
        st.caption("*(Dihitung dengan skema gross-up agar vendor menerima nilai Netto secara utuh)*")
    
    # Penjelasan Aturan
    with st.expander("Lihat Detail Aturan & Catatan"):
        st.write(f"1. Transaksi diklasifikasikan sebagai **{kat_input}** dengan tarif PPh sebesar **{pph_rate*100:g}%**.")
        
        if gross <= 2000000:
            if kategori_engine == "Barang":
                st.info("Catatan: Karena nilai bruto ≤ Rp 2.000.000, maka tidak dipungut PPN & PPh 22 sesuai ketentuan bendahara pemerintah.")
            else:
                st.info("Catatan: Karena nilai bruto ≤ Rp 2.000.000, maka tidak dipungut PPN. Namun, PPh atas jasa/sewa tetap dikenakan tanpa batas minimum.")
        
        if kat_input == "Barang" and not npwp_input and gross > 2000000:
            st.warning("Peringatan: Tarif PPh 22 dikenakan 100% lebih tinggi karena vendor tidak memiliki NPWP.")
        elif kat_input == "Jasa (PPh 23)" and not npwp_input:
            st.warning("Peringatan: Tarif PPh 23 dikenakan 100% lebih tinggi karena vendor tidak memiliki NPWP.")

st.divider()
with st.expander("☕ Support Developer"):
    st.markdown("Jika aplikasi ini membantu mempercepat pekerjaan Anda, Anda dapat memberikan dukungan ke developer melalui QRIS di bawah ini:")
    st.image("qris.jpeg", width=350)
