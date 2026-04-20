import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
from streamlit_option_menu import option_menu
from frontend_streamLit.login_frontend import login_page, signup_page, choose_action
from diff_pages import Home, QExperiment_Display, QExperiment_showcase, flowChartProto

# 1. Config FIRST
# st.set_page_config(layout="centered")

# 2. Initialize Session State
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "username" not in st.session_state:
    st.session_state.username = "jovin"

# 3. If logged in, show sidebar navigation
if st.session_state.username != "":
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}")
        st.success("Select an experiment below:")
        st.divider()

        # Update session state directly with the menu choice
        st.session_state.page = option_menu(
            menu_title=None,
            # options=["Home", "Quantum Experiment Data Entry", "Quantum Experiment Display", "Noise Injection Experiment", "Circuit Compress & Predict"],
            options=["Home", "Circuit Compress & Predict", 'Circuit FlowChart Builder'],
            icons=["house", "gear", "gear"],
            default_index=0
        )

# 4. Page Routing
if st.session_state.username == "":
    # This shows the tabs for login/signup if not logged in
    choose_action()
else:
    # This handles navigation AFTER login
    if st.session_state.page == "Home":
        Home.home_page()
    elif st.session_state.page == "Quantum Experiment Display":
        QExperiment_Display.display_page()
    elif st.session_state.page == "Circuit Compress & Predict":
        # QExpeiment_CircuitCompressPerformance.page()
        QExperiment_showcase.page()
    elif st.session_state.page == 'Circuit FlowChart Builder':
        flowChartProto.flow_page()