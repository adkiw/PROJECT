import sqlite3
from datetime import date

# Database connection
@st.cache(allow_output_mutation=True)
def get_connection(db_path='dispo.db'):
    return sqlite3.connect(db_path, check_same_thread=False)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

conn = get_connection()
c = conn.cursor()

# Main UI
def show(conn, c):
st.title("DISPO – Vilkikų valdymas")

    # Naujo vilkiko įvedimo forma
    # fetch available trailers
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]

    # —————————————
    # NEW TRUCK FORM
    # —————————————
with st.form("vilkikai_forma", clear_on_submit=True):
        num = st.text_input("Vilkiko numeris")
        marke = st.text_input("Markė")
        metai = st.text_input("Pagaminimo metai")
        tech = st.date_input("Tech. apžiūra", value=date.today())
        vadyb = st.text_input("Transporto vadybininkas")
        vair = st.text_input("Vairuotojai (kableliais)")
        priekabu = [r[0] for r in c.execute("SELECT numeris FROM priekabos")]
        priek = st.selectbox("Priekaba", [""] + priekabu)
        ok = st.form_submit_button("Išsaugoti vilkiką")
    if ok:
        if not num:
            st.warning("Įveskite numerį.")
        numeris     = st.text_input("Vilkiko numeris")
        marke       = st.text_input("Markė")
        pag_metai   = st.text_input("Pagaminimo metai")
        tech_apz    = st.date_input("Tech. apžiūra", value=date.today())
        vadyb       = st.text_input("Transporto vadybininkas")
        vair        = st.text_input("Vairuotojai (atskirti kableliais)")
        priekabu_pasirinkimai = [""] + priekabu_sarasas
        priek       = st.selectbox("Priekaba", priekabu_pasirinkimai)
        sub         = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
else:
try:
                c.execute(
                    "INSERT INTO vilkikai VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (num, marke, int(metai or 0), str(tech), vadyb, vair, priek)
                )
                c.execute("""
                    INSERT INTO vilkikai (
                        numeris, marke, pagaminimo_metai, tech_apziura,
                        vadybininkas, vairuotojai, priekaba
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (numeris, marke, int(pag_metai or 0), str(tech_apz),
                      vadyb, vair, priek))
conn.commit()
                st.success("Vilkikas išsaugotas.")
                st.experimental_rerun()
                st.success("✅ Išsaugota sėkmingai.")
except Exception as e:
                st.error(f"Klaida: {e}")
                st.error(f"❌ Klaida: {e}")

    # Lentelė ir bendras priekabų priskyrimas
    # —————————————
    # EXISTING TRUCKS TABLE
    # —————————————
    st.subheader("📋 Vilkikų sąrašas")
df = pd.read_sql_query("SELECT * FROM vilkikai", conn)

if df.empty:
        st.info("Nėra vilkikų. Pridėkite naują.")
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
return
    st.subheader("Vilkikų sąrašas")

    # show the raw table first
st.dataframe(df, use_container_width=True)

    st.markdown("### Bendras priekabų priskyrimas")
    vilkikai = df['numeris'].tolist()
    pasirinktas = st.selectbox("Vilkikas", vilkikai)
    # —————————————
    # BENDRAS PRIEKABŲ PRISKYRIMAS
    # —————————————
    st.markdown("### 🔄 Bendras priekabų priskyrimas")

    # 1) Pasirenkame vilkiką
    vilkiku_sarasas = df['numeris'].tolist()
    selected_vilkikas = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)

    # 2) Paruošiame priekabų sąrašą su spalvotais ženklais
uzimtos = set(df['priekaba'].dropna())
    options = [""] + [
        f"{pr} — {'užimta' if pr in uzimtos else 'laisva'}"
        for pr in priekabu
    ]
    sel = st.selectbox("Priekaba", options)
    trailer_options = [""]
    for pr in priekabu_sarasas:
        label = f"{pr} — " + ("🔴 užimta" if pr in uzimtos else "🟢 laisva")
        trailer_options.append(label)

    selected_label = st.selectbox("Pasirinkite priekabą", trailer_options)

    if st.button("Priskirti priekabą"):
        if not pasirinktas or not sel:
            st.warning("Pasirinkite vilkiką ir priekabą.")
    # 3) Mygtukas priskyrimui
    if st.button("💾 Priskirti priekabą"):
        if not selected_vilkikas or not selected_label:
            st.warning("⚠️ Pasirinkite vilkiką ir priekabą.")
else:
            nr = sel.split()[0]
            # išrinkame numerį be ženkliukų
try:
                new_priek = selected_label.split()[0]
c.execute(
"UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                    (nr, pasirinktas)
                    (new_priek, selected_vilkikas)
)
conn.commit()
                st.success(f"Priekaba {nr} priskirta {pasirinktas}.")
                st.experimental_rerun()
                st.success(f"✅ Priekaba {new_priek} priskirta vilkikui {selected_vilkikas}.")
except Exception as e:
                st.error(f"Klaida: {e}")
                st.error(f"❌ Klaida priskiriant: {e}")

if __name__ == "__main__":
show(conn, c)
