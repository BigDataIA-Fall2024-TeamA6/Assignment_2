import streamlit as st
from pages.db import DBConnection

st.header("Create User Page")

firstname = st.text_input("First Name",key="fname")
lastname = st.text_input("Last Name",key="lname")
username = st.text_input("Username",key="uname")
password = st.text_input("Password",type="password",key="pword")
user_type = st.text_input("User Type",key="utype")

if st.button("Submit"):
    if firstname and lastname and username and password:
        st.success("Account created")
        st.switch_page("pages/login.py")
    else:
        st.error("All fields required!")