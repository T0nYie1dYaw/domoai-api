import os

import streamlit as st
from streamlit_authenticator import Authenticate


def check_password():
    STREAMLIT_AUTH = os.environ.get("STREAMLIT_AUTH")

    if not STREAMLIT_AUTH:
        return True

    username, password = STREAMLIT_AUTH.split(":")

    if not username or not password:
        return True

    """Returns `True` if the user had a correct password."""

    authenticator = Authenticate(
        credentials={"usernames": {username: {"email": "demo@example.com", "name": "demo", "password": password}}},
        cookie_name="domo_ai_demo",
        cookie_key="zgt!uay.aug4juv*FAF"
    )

    name, authentication_status, username = authenticator.login('main')

    if authentication_status:
        st.markdown("""
            <style>
            div[data-testid='stSidebarNav'] ul {max-height:none}</style>
            """, unsafe_allow_html=True)
        with st.sidebar.container():
            authenticator.logout('Logout', 'main')
        return True
    elif authentication_status == False:
        st.error('Username/password is incorrect')
        return False
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        return False
