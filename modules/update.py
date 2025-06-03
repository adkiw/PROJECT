import streamlit as st
import pandas as pd
from datetime import datetime

SUGGEST_PAKROVIMAS = ["Problema", "Atvyko", "Pakrautas"]
SUGGEST_ISKROVIMAS = ["Problema", "Atvyko", "Iškrautas"]

def autocomplete_input(label, allowed_words, key):
    val = st.text_input(label, key=key)
    show_suggest = val and any(w.lower().startswith(val.lower()) for w in allowed_words)
    suggestion_clicked = False

    if show_suggest:
        suggestions = [w for w in allowed_words if w.lower().startswith(val.lower())]
        for sugg in suggestions:
            if st.button(f"➤ {sugg}", key=f"{key}_{sugg}"):
                st.session_state[key] = sugg
                suggestion_clicked = True
                val = sugg

    # Validacija: leidžiamas tik laikas arba leistinas žodis
    def is_time_format(v):
        try:
            h, m = map(int, v.split(":"))
            return 0 <= h < 24 and 0 <= m < 60
        except: return False

    if val and val not in allowed_words and not is_time_format(val):
        st.error("Leidžiama įrašyti tik laiką (pvz 08:00) arba: " + ", ".join(allowed_words))
    return val

def show(conn, c):
    st.title("DEMO – Vienas įvesties laukas, su autocomplete ir validacija")
    st.write("Pakrovimui:")
    pakrovimas = autocomplete_input("Atvykimo į pakrovimą", SUGGEST_PAKROVIMAS, "pakrovimas_demo")
    st.write("Iškrovimui:")
    iskovimas = autocomplete_input("Atvykimo į iškrovimą", SUGGEST_ISKROVIMAS, "iskrovimas_demo")

# Jei reikia pilnai perkelti į tavo lentelės logiką – žinok, tą autocomplete_input funkciją naudoji
# lentelės stulpelyje, VIENOJE vietoje, o ne per dvi.

# Pvz.:

# st.columns(...)
# pakrovimo_input = autocomplete_input("", SUGGEST_PAKROVIMAS, key=f"pk_{k[0]}")
# ... ir pan.

