import streamlit as st
from modules import dispo, kroviniai, vilkikai, priekabos, grupes, vairuotojai, klientai, darbuotojai, nustatymai
from db import init_db

st.set_page_config(layout="wide")
conn, c = init_db()

# Moduliai
moduliai = ["Dispo", "Kroviniai", "Vilkikai", "Priekabos", "Grupės", "Vairuotojai", "Klientai", "Darbuotojai", "Nustatymai"]
modulis = st.sidebar.radio("📂 Pasirink modulį", moduliai)

# Kiekvieno modulio kvietimas
if modulis == "Dispo":
    dispo.show(conn, c)
elif modulis == "Kroviniai":
    kroviniai.show(conn, c)
elif modulis == "Vilkikai":
    vilkikai.show(conn, c)
elif modulis == "Priekabos":
    priekabos.show(conn, c)
elif modulis == "Grupės":
    grupes.show(conn, c)
elif modulis == "Vairuotojai":
    vairuotojai.show(conn, c)
elif modulis == "Klientai":
    klientai.show(conn, c)
elif modulis == "Darbuotojai":
    darbuotojai.show(conn, c)
elif modulis == "Nustatymai":
    nustatymai.show(conn, c)
