import streamlit as st

from streamlit_demo.auth import check_password

st.set_page_config(page_title="DomoAI API")


if not check_password():
    st.stop()

st.title("Unofficial DomoAI API Demo")
st.link_button(label='GitHub', url='https://github.com/T0nYie1dYaw/domoai-api')
