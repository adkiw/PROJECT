import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

def show(conn, c):
    st.title("Užsakymų valdymas")

    # Užkraunam duomenis
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
    if df.empty:
        st.info("Kol kas nėra krovinių.")
        return

    # Paieška ir filtrai viršuje
    with st.expander("🔍 Filtruoti krovinį"):
        f_klientas = st.text_input("Filtruoti pagal klientą")
        f_salis = st.text_input("Filtruoti pagal šalį (pakrovimo ar iškrovimo)")
        f_miestas = st.text_input("Filtruoti pagal miestą (pakrovimo ar iškrovimo)")
        f_busena = st.text_input("Filtruoti pagal būseną")

    df_f = df.copy()
    if f_klientas:
        df_f = df_f[df_f['klientas'].str.contains(f_klientas, case=False, na=False)]
    if f_salis:
        df_f = df_f[df_f['pakrovimo_salis'].str.contains(f_salis, case=False, na=False) | 
                    df_f['iskrovimo_salis'].str.contains(f_salis, case=False, na=False)]
    if f_miestas:
        df_f = df_f[df_f['pakrovimo_miestas'].str.contains(f_miestas, case=False, na=False) |
                    df_f['iskrovimo_miestas'].str.contains(f_miestas, case=False, na=False)]
    if f_busena:
        df_f = df_f[df_f['busena'].str.contains(f_busena, case=False, na=False)]

    # Kortelių rodymas (pagal pavyzdį)
    st.markdown("---")
    st.markdown("#### Kroviniai:")

    # Kortelės stilius
    for idx, row in df_f.iterrows():
        with st.container():
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; border: 1px solid #eee; border-radius: 15px; padding: 15px; margin-bottom: 15px; box-shadow: 2px 2px 8px #eee;">
                    <div style="flex:0 0 60px; text-align:center; font-size:40px; margin-right:20px;">
                        🚚
                    </div>
                    <div style="flex:1;">
                        <b>{row['klientas']}</b><br>
                        <small><b>Užsakymo nr.:</b> {row['uzsakymo_numeris']}</small><br>
                        <b>Pakrovimas:</b> {row['pakrovimo_salis']}, {row['pakrovimo_miestas']}<br>
                        <b>Iškrovimas:</b> {row['iskrovimo_salis']}, {row['iskrovimo_miestas']}<br>
                        <b>Data:</b> {row['pakrovimo_data']} – {row['iskrovimo_data']}<br>
                        <b>Vilkikas:</b> {row['vilkikas']} | <b>Priekaba:</b> {row['priekaba']}
                    </div>
                    <div style="min-width:120px; text-align:center;">
                        <span style="display:inline-block; background:#f0f2f6; padding:8px 14px; border-radius:8px; font-weight:bold;">
                            {row['busena']}
                        </span><br><br>
                        <button onclick="window.location.href='/?edit={row['id']}'" style="border:none; background:#eaeaea; padding:7px 10px; border-radius:6px; cursor:pointer;">
                            ✏️ Redaguoti
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
    # Pridėti naują krovinį
    st.button("➕ Pridėti naują krovinį")

    # Eksportas
    csv = df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button("💾 Eksportuoti kaip CSV", data=csv, file_name="kroviniai.csv", mime="text/csv")

