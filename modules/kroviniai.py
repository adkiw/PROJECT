import streamlit as st
import pandas as pd
from datetime import date, timedelta

EU_COUNTRIES = [
    ("", ""), ("Lietuva", "LT"), ("Latvija", "LV"), ("Estija", "EE"), ("Lenkija", "PL"), ("Vokietija", "DE"),
    ("Prancūzija", "FR"), ("Ispanija", "ES"), ("Italija", "IT"), ("Olandija", "NL"), ("Belgija", "BE"),
    ("Austrija", "AT"), ("Švedija", "SE"), ("Suomija", "FI"), ("Čekija", "CZ"), ("Slovakija", "SK"),
    ("Vengrija", "HU"), ("Rumunija", "RO"), ("Bulgarija", "BG"), ("Danija", "DK"), ("Norvegija", "NO"),
    ("Šveicarija", "CH"), ("Kroatija", "HR"), ("Slovėnija", "SI"), ("Portugalija", "PT"), ("Graikija", "GR"),
    ("Airija", "IE"), ("Didžioji Britanija", "GB"),
]

HEADER_LABELS = {
    "id": "ID",
    "busena": "Būsena",
    "pakrovimo_data": "Pakr.<br>data",
    "iskrovimo_data": "Iškr.<br>data",
    "pakrovimo_salis": "Pakr.<br>šalis",
    "pakrovimo_regionas": "Pakr.<br>reg.",
    "pakrovimo_miestas": "Pakr.<br>miest.",
    "iskrovimo_salis": "Iškr.<br>šalis",
    "iskrovimo_regionas": "Iškr.<br>reg.",
    "iskrovimo_miestas": "Iškr.<br>miest.",
    "klientas": "Klientas",
    "vilkikas": "Vilkikas",
    "priekaba": "Priekaba",
    "ekspedicijos_vadybininkas": "Eksp.<br>vadyb.",
    "transporto_vadybininkas": "Transp.<br>vadyb.",
    "uzsakymo_numeris": "Užsak.<br>nr.",
    "kilometrai": "Km",
    "frachtas": "Frachtas",
    "pakrovimo_numeris": "Pakr.<br>nr.",
    "pakrovimo_laikas_nuo": "Pakr.<br>nuo",
    "pakrovimo_laikas_iki": "Pakr.<br>iki",
    "pakrovimo_adresas": "Pakr.<br>adr.",
    "iskrovimo_adresas": "Iškr.<br>adr.",
    "iskrovimo_laikas_nuo": "Iškr.<br>nuo",
    "iskrovimo_laikas_iki": "Iškr.<br>iki",
    "atsakingas_vadybininkas": "Atsak.<br>vadyb.",
    "svoris": "Svoris",
    "paleciu_skaicius": "Pad.<br>sk.",
    "pakrovimo_vieta": "Pakr.<br>vieta",
    "iskrovimo_vieta": "Iškr.<br>vieta",
}

FIELD_ORDER = [
    "id", "busena", "pakrovimo_data", "iskrovimo_data", "pakrovimo_salis", "pakrovimo_regionas",
    "pakrovimo_miestas", "pakrovimo_vieta", "iskrovimo_salis", "iskrovimo_regionas",
    "iskrovimo_miestas", "iskrovimo_vieta", "klientas", "vilkikas", "priekaba",
    "ekspedicijos_vadybininkas", "transporto_vadybininkas",
    "uzsakymo_numeris", "kilometrai", "frachtas", "pakrovimo_numeris",
    "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki", "pakrovimo_adresas",
    "iskrovimo_adresas", "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
    "atsakingas_vadybininkas", "svoris", "paleciu_skaicius"
]

def show(conn, c):
    st.title("Užsakymų valdymas")
    add_clicked = st.button("➕ Pridėti naują krovinį", use_container_width=True)

    # Užtikrinti laukus DB
    existing = [r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
    extras = {
        "pakrovimo_numeris": "TEXT", "pakrovimo_laikas_nuo": "TEXT", "pakrovimo_laikas_iki": "TEXT",
        "pakrovimo_salis": "TEXT", "pakrovimo_regionas": "TEXT", "pakrovimo_miestas": "TEXT",
        "pakrovimo_adresas": "TEXT", "pakrovimo_data": "TEXT",
        "iskrovimo_salis": "TEXT", "iskrovimo_regionas": "TEXT", "iskrovimo_miestas": "TEXT",
        "iskrovimo_adresas": "TEXT", "iskrovimo_data": "TEXT", "iskrovimo_laikas_nuo": "TEXT",
        "iskrovimo_laikas_iki": "TEXT", "vilkikas": "TEXT", "priekaba": "TEXT",
        "atsakingas_vadybininkas": "TEXT", "ekspedicijos_vadybininkas": "TEXT",
        "transporto_vadybininkas": "TEXT",
        "pakrovimo_vieta": "TEXT", "iskrovimo_vieta": "TEXT",
        "kilometrai": "INTEGER", "frachtas": "REAL", "svoris": "INTEGER", "paleciu_skaicius": "INTEGER", "busena": "TEXT"
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # ---- Duomenų pasirinkimai ----
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    if len(klientai) == 0:
        st.warning("Nėra nė vieno kliento! Pridėkite klientą modulyje **Klientai** ir grįžkite čia.")
        return

    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    vilkikai_df = pd.read_sql_query("SELECT numeris, vadybininkas FROM vilkikai", conn)
    vilk_vad_map = {r['numeris']: r['vadybininkas'] for _, r in vilkikai_df.iterrows()}

    # --- Sąrašas ir filtrai ---
    if 'selected_cargo' not in st.session_state:
        st.session_state['selected_cargo'] = None
    if add_clicked:
        st.session_state['selected_cargo'] = 0
    def clear_sel():
        st.session_state['selected_cargo'] = None
        for k in list(st.session_state):
            if k.startswith("f_"):
                st.session_state[k] = ""
    def edit_cargo(cid): st.session_state['selected_cargo'] = cid
    sel = st.session_state['selected_cargo']

    if sel is None:
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("Kol kas nėra krovinių.")
        else:
            # Automatiškai užpildome transporto vadybininką pagal vilkiką
            df["transporto_vadybininkas"] = df["vilkikas"].map(vilk_vad_map).fillna("")
            papildomi = [c for c in df.columns if c not in FIELD_ORDER]
            saraso_stulpeliai = FIELD_ORDER + papildomi
            df_disp = df[saraso_stulpeliai].fillna("")

            st.markdown("""
                <style>
                .stDataFrame { overflow-x: auto; }
                .stDataFrame thead tr th { white-space: normal; word-break: keep-all; }
                .stDataFrame tbody tr td { white-space: normal; word-break: keep-all; }
                /* Ištrinamas žymeklis selectbox sąraše */
                div[role="option"] svg { display: none !important; }
                </style>
            """, unsafe_allow_html=True)

            # Filtravimo laukai virš stulpelių
            filter_cols = st.columns(len(df_disp.columns)+1)
            for i, col in enumerate(df_disp.columns):
                filter_cols[i].text_input("", key=f"f_{col}", label_visibility="collapsed")
            filter_cols[-1].write("")

            df_f = df_disp.copy()
            for col in df_disp.columns:
                v = st.session_state.get(f"f_{col}", "")
                if v:
                    df_f = df_f[df_f[col].astype(str).str.contains(v, case=False, na=False)]

            hdr = st.columns(len(df_disp.columns)+1)
            for i, col in enumerate(df_disp.columns):
                label = HEADER_LABELS.get(col, col.replace("_", "<br>")[:14])
                hdr[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)
            hdr[-1].markdown("<b>Veiksmai</b>", unsafe_allow_html=True)

            for _, row in df_f.iterrows():
                row_cols = st.columns(len(df_disp.columns)+1)
                for i, col in enumerate(df_disp.columns):
                    row_cols[i].write(row[col])
                row_cols[-1].button("✏️", key=f"edit_{row['id']}", on_click=edit_cargo, args=(row['id'],))

            st.download_button(
                "💾 Eksportuoti kaip CSV",
                data=df_disp.to_csv(index=False, sep=';').encode('utf-8'),
                file_name="kroviniai.csv",
                mime="text/csv"
            )
        return

    # --- Forma ---
    is_new = (sel == 0)
    data = {} if is_new else pd.read_sql_query(
        "SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,)
    ).iloc[0]
    if not is_new and data.empty:
        st.error("Įrašas nerastas."); clear_sel(); return

    st.markdown("### Krovinių įvedimas / redagavimas")
    colA, colB, colC, colD = st.columns(4)
    with st.form("cargo_form", clear_on_submit=False):
        # Klientas
        opts_k = [""] + klientai
        idx_k = 0 if is_new else opts_k.index(data.get('klientas', ''))
        klientas = colA.selectbox("Klientas", opts_k, index=idx_k, key="kl_klientas")
        df_klientai = pd.read_sql_query("SELECT pavadinimas, likes_limitas FROM klientai", conn)
        klientu_limitai = {row['pavadinimas']: row['likes_limitas'] for _, row in df_klientai.iterrows()}
        limito_likutis = klientu_limitai.get(klientas, "")
        if klientas:
            colA.info(f"Limito likutis: {limito_likutis}")

        uzsak = colA.text_input(
            "Užsakymo nr.", value=("" if is_new else data.get('uzsakymo_numeris', "")), key="kl_uzsak"
        )

        busena_opt = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)).fetchall()]
        if not busena_opt:
            busena_opt = ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]
        bus_idx = 0 if is_new or data.get('busena') not in busena_opt else busena_opt.index(data['busena'])
        bus = colA.selectbox("Būsena", busena_opt, index=bus_idx, key="cr_busena")

        # Ekspedicijos vadybininkas (tik rodoma, nepasirenkama)
        eksped_val = "" if is_new else data.get('ekspedicijos_vadybininkas', "")
        colA.text_input("Ekspedicijos vadybininkas", value=eksped_val, disabled=True)

        # Pakrovimo dalis
        pk_data = colB.date_input(
            "Pakrovimo data",
            value=(date.today() if is_new else pd.to_datetime(data['pakrovimo_data']).date()),
            key="pk_data"
        )
        pk_salis_opts = [f"{n} ({c})" for n, c in EU_COUNTRIES]
        pk_salis_index = 0
        if not is_new:
            try:
                # surandame įrašytą kodą sąraše
                existing_code = data.get('pakrovimo_salis', "")
                pk_salis_index = next(
                    i for i, x in enumerate(pk_salis_opts) if f"({existing_code})" in x
                )
            except StopIteration:
                pk_salis_index = 0
        pk_salis = colB.selectbox("Pakrovimo šalis", pk_salis_opts, index=pk_salis_index, key="pk_sal")

        pk_regionas = colB.text_input(
            "Pakrovimo regionas",
            value=("" if is_new else data.get('pakrovimo_regionas', "")),
            key="pk_regionas"
        )

        # Sukuriame pakrovimo vietą: šalis_kodas + regionas
        prefix_pk = pk_salis.split("(")[-1][:-1] if "(" in pk_salis else ""
        pakrovimo_vieta = f"{prefix_pk}{pk_regionas}" if prefix_pk and pk_regionas else ""
        colB.text_input("Pakrovimo vieta", value=pakrovimo_vieta, disabled=True)

        # Likę laukai paliekame, jei reikia: miestas, adresas
        pk_mie = colB.text_input(
            "Pakrovimo miestas",
            value=("" if is_new else data.get('pakrovimo_miestas', "")),
            key="pk_mie"
        )
        pk_adr = colB.text_input(
            "Pakrovimo adresas",
            value=("" if is_new else data.get('pakrovimo_adresas', "")),
            key="pk_adr"
        )

        # Pakrovimo laikas nuo / iki
        pk_nuo = colB.time_input(
            "Pakrovimo laikas nuo",
            value=(date.today().replace(hour=8, minute=0).time() if is_new else pd.to_datetime(data['pakrovimo_laikas_nuo']).time()),
            key="pk_nuo"
        )
        pk_iki = colB.time_input(
            "Pakrovimo laikas iki",
            value=(date.today().replace(hour=17, minute=0).time() if is_new else pd.to_datetime(data['pakrovimo_laikas_iki']).time()),
            key="pk_iki"
        )

        # Iškrovimo dalis
        isk_data = colC.date_input(
            "Iškrovimo data",
            value=(pk_data + timedelta(days=1) if is_new else pd.to_datetime(data['iskrovimo_data']).date()),
            key="isk_data"
        )
        is_salis_opts = pk_salis_opts
        is_salis_index = 0
        if not is_new:
            try:
                existing_is_code = data.get('iskrovimo_salis', "")
                is_salis_index = next(
                    i for i, x in enumerate(is_salis_opts) if f"({existing_is_code})" in x
                )
            except StopIteration:
                is_salis_index = 0
        is_salis = colC.selectbox("Iškrovimo šalis", is_salis_opts, index=is_salis_index, key="is_sal")

        is_regionas = colC.text_input(
            "Iškrovimo regionas",
            value=("" if is_new else data.get('iskrovimo_regionas', "")),
            key="is_regionas"
        )

        # Sukuriame iškrovimo vietą: šalis_kodas + regionas
        prefix_is = is_salis.split("(")[-1][:-1] if "(" in is_salis else ""
        iskrovimo_vieta = f"{prefix_is}{is_regionas}" if prefix_is and is_regionas else ""
        colC.text_input("Iškrovimo vieta", value=iskrovimo_vieta, disabled=True)

        # Likę laukai paliekame, jei reikia: miestas, adresas
        is_mie = colC.text_input(
            "Iškrovimo miestas",
            value=("" if is_new else data.get('iskrovimo_miestas', "")),
            key="is_mie"
        )
        is_adr = colC.text_input(
            "Iškrovimo adresas",
            value=("" if is_new else data.get('iskrovimo_adresas', "")),
            key="is_adr"
        )

        # Iškrovimo laikas nuo / iki
        is_nuo = colC.time_input(
            "Iškrovimo laikas nuo",
            value=(date.today().replace(hour=8, minute=0).time() if is_new else pd.to_datetime(data['iskrovimo_laikas_nuo']).time()),
            key="is_nuo"
        )
        is_iki = colC.time_input(
            "Iškrovimo laikas iki",
            value=(date.today().replace(hour=17, minute=0).time() if is_new else pd.to_datetime(data['iskrovimo_laikas_iki']).time()),
            key="is_iki"
        )

        # Vilkikas
        v_opts = [""] + vilkikai
        v_idx = 0 if is_new else v_opts.index(data.get('vilkikas', "")) if data.get('vilkikas', "") in v_opts else 0
        vilk = colD.selectbox("Vilkikas", v_opts, index=v_idx, key="cr_vilk")

        # Transporto vadybininkas – automatiškai pagal vilkiką, nepasirenkamas
        transp_vad = vilk_vad_map.get(vilk, "") if vilk else ""
        colD.text_input("Transporto vadybininkas", value=transp_vad, disabled=True)

        # Priekaba, Km, Frachtas, Svoris, Padėklų sk.
        priekaba_value = ""
        if vilk:
            res = c.execute("SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilk,)).fetchone()
            priekaba_value = res[0] if res and res[0] else ""
        colD.text_input("Priekaba", priekaba_value, disabled=True, key="cr_priek")
        km = colD.text_input("Km", value=("" if is_new else str(data.get('kilometrai', 0))), key="cr_km")
        fr = colD.text_input("Frachtas (€)", value=("" if is_new else str(data.get('frachtas', 0))).replace(".", ","), key="cr_fr")
        sv = colD.text_input("Svoris (kg)", value=("" if is_new else str(data.get('svoris', 0))), key="cr_sv")
        pal = colD.text_input("Padėklų sk.", value=("" if is_new else str(data.get('paleciu_skaicius', 0))), key="cr_pal")

        save = st.form_submit_button("💾 Išsaugoti")
        back = st.form_submit_button("🔙 Grįžti į sąrašą", on_click=clear_sel)

    if save:
        frachtas_float = float(fr.replace(",", ".") or 0)
        km_float = int(km or 0)
        limito_likutis = klientu_limitai.get(klientas, None)

        if pk_data > isk_data:
            st.error("Pakrovimo data negali būti vėlesnė už iškrovimo.")
        elif not klientas or not uzsak:
            st.error("Privalomi laukai: Klientas ir Užsakymo nr.")
        elif limito_likutis is not None and frachtas_float > limito_likutis:
            st.error(f"Kliento limito likutis ({limito_likutis}) yra mažesnis nei frachtas ({frachtas_float}). Negalima išsaugoti.")
        else:
            vals = {
                'klientas': klientas,
                'uzsakymo_numeris': uzsak,
                'pakrovimo_salis': pk_salis.split("(")[-1][:-1] if "(" in pk_salis else pk_salis,
                'pakrovimo_regionas': pk_regionas,
                'pakrovimo_miestas': pk_mie,
                'pakrovimo_adresas': pk_adr,
                'pakrovimo_data': pk_data.isoformat(),
                'pakrovimo_laikas_nuo': pk_nuo.isoformat(),
                'pakrovimo_laikas_iki': pk_iki.isoformat(),
                'iskrovimo_salis': is_salis.split("(")[-1][:-1] if "(" in is_salis else is_salis,
                'iskrovimo_regionas': is_regionas,
                'iskrovimo_miestas': is_mie,
                'iskrovimo_adresas': is_adr,
                'iskrovimo_data': isk_data.isoformat(),
                'iskrovimo_laikas_nuo': is_nuo.isoformat(),
                'iskrovimo_laikas_iki': is_iki.isoformat(),
                'vilkikas': vilk,
                'priekaba': priekaba_value,
                'transporto_vadybininkas': transp_vad,
                'ekspedicijos_vadybininkas': eksped_val,
                'kilometrai': km_float,
                'frachtas': frachtas_float,
                'svoris': int(sv or 0),
                'paleciu_skaicius': int(pal or 0),
                'busena': bus,
                'pakrovimo_vieta': pakrovimo_vieta,
                'iskrovimo_vieta': iskrovimo_vieta
            }
            try:
                if is_new:
                    cols = ",".join(vals.keys())
                    q = f"INSERT INTO kroviniai ({cols}) VALUES ({','.join(['?']*len(vals))})"
                    c.execute(q, tuple(vals.values()))
                else:
                    set_str = ",".join(f"{k}=?" for k in vals)
                    q = f"UPDATE kroviniai SET {set_str} WHERE id=?"
                    c.execute(q, tuple(vals.values()) + (sel,))
                conn.commit()
                st.success("✅ Krovinys išsaugotas.")
                clear_sel()
            except Exception as e:
                st.error(f"❌ Klaida: {e}")
