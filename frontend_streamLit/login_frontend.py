import streamlit as st
import requests
import time
from diff_pages import Home

# if "page" not in st.session_state:
#     st.session_state.page = "default"

def login_page():
    FASTAPI_URL = "http://127.0.0.1:8000/login"
    st.markdown("#Login Page")
    username = ""
    password = ""

    username = st.text_input("Username:", key="login_username")
    password = st.text_input("Password:", type="password", key="login_password")
    login = st.button("LOGIN", key="login_btn")

    # ret = "login"

    if login and username != "" and password != "": 
        response = requests.post(FASTAPI_URL, json={"username": username, "password": password})
        st.write(f"Status: {response.status_code}, Response: {response.json()}")

        if response.status_code == 200:
            st.success("Login successful!")
            st.session_state.page = "Home"
            st.session_state.username = response.json().get("username", "")
            st.subheader(f"Welcome, {st.session_state.username}!")
            st.rerun()

        else:
            st.error("Invalid credentials. Please try again. Or if you are New , Sign Up First")
        pass

    else: 
        st.error("Please enter both username and password")
    # return ret

def signup_page():
    FASTAPI_URL = "http://127.0.0.1:8000/signup"
    st.markdown("#SignUp Page")
    username = ""
    password = ""
    reenter = ""


    username = st.text_input("Enter a username:", key = "signup_username")
    password = st.text_input("Password:", type="password", key = "signup_password")
    reenter = st.text_input("ReEnter Password:", type = "password", key = "signup_reenter")

    signup = st.button("SIGNUP", key = "signup_btn")
    # ret = "signup"

    if signup:
        # st.subheader(password)
        # st.subheader(reenter)

        if password == reenter:
            # st.subheader("DONE")
            response = requests.post(FASTAPI_URL, json={"username": username, "password": password})
            if response.status_code == 200:
                st.success("Signup successful! You can now log in.")
                st.session_state.page = "Home"
                st.session_state.username = response.json().get("username", "")
                st.rerun()

            elif response.status_code == 400:
                st.error("Username already exists. Please choose a different username. IF EXISTING USER, LOGIN INSTEAD")

            else: 
                st.error("Signup failed. Please try again.")

        else: 
            signup = False
            st.error("Passwords do not match <br> try again")
            # st.subheader("Password mismatch")
    # return ret

def choose_action():
    # col1, col2, col3 = st.columns([1, 2, 1])
    # with col2:
    #     st.markdown("<div style='text-align: center'><h3>Login/Signup</h3></div>", unsafe_allow_html=True)
    #     btn_col1, btn_col2 = st.columns(2)
    #     with btn_col1:
    #         if st.button("Login", key="choose_login_btn"):
    #             st.session_state.page = "login"
    #     with btn_col2:
    #         if st.button("Sign Up", key="choose_signup_btn"):
    #             st.session_state.page = "signup"

    # if st.session_state.page == "login":
    #     login_page()
    # elif st.session_state.page == "signup":
    #     signup_page()

    # col1, col2, col3 = st.columns([1, 2, 1])
    # ret = "default"
    # with col2:
    #     st.markdown("<div style='text-align: center'><h3>Login/Signup</h3></div>", unsafe_allow_html=True)
    #     btn_col1, btn_col2 = st.columns(2)
    #     with btn_col1:
    #         if st.button("Login"):
    #             ret = "login"
    #             st.rerun()
    #     with btn_col2:
    #         if st.button("Sign Up"):
    #             ret = "signup"
    #             st.rerun()

    with st.container(border = True, key = "green_container"):
        st.html(f"<style>{Home.css}</style>")
        st.markdown("<h2 style='text-align: center;'>Welcome to Quantum Experiments</h2>", unsafe_allow_html=True)
        
        
        # Using tabs as a "toggle" for the login/signup forms
        login, signup = st.tabs(["Login", "Sign Up"])

        with login:
            # Instead of returning a value, just call the function here
            login_page()
            
        with signup:
            # Call the signup function directly here
            signup_page()

# choose_action()
