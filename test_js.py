import streamlit as st
from streamlit_javascript import st_javascript

st.write("Bandymas")
ret = st_javascript(js_code="console.log('Labas iš JS!');", args={})
st.write(ret)
