
import streamlit as st
from diff_pages import Home as home
import requests
import pandas as pd
import io
from qiskit import qpy
import base64
# from diff_pages import QExperiment_NoiseInjection

def display_page():

    
    st.set_page_config(layout="wide")       
    FASTAPI_URL = "http://127.0.0.1:8000/expdata_retrieve"
    st.set_page_config("QExp_Display")


    if "showExp" not in st.session_state:
        st.session_state.showExp = False
    if "disp_exp" not in st.session_state:
        st.session_state.disp_exp = False


    
    with st.container(border = True, key = "green_container"):
        st.html(f"<style>{home.css}</style>")
        st.header("Experiment Display page")

        response = requests.get(url = FASTAPI_URL, params = {"username":st.session_state.username})
        # st.write(st.session_state.username)

        # st.write(response)
        # st.write(response.keys())
        

        if response.status_code == 200: 
            with st.container(border = True):
                exp_data = response.json()
                df = pd.DataFrame(exp_data)
                # st.write(exp_data)
                # st.write(df.columns)
                df_nodata_nocirc = df[["username", "experiment_name", "upload_date","experiment_noise_date"]].sort_values("upload_date",ascending=False, ignore_index=True)
                df = df.sort_values("upload_date", ascending = False, ignore_index=True)

                # st.write(df_nodata_nocirc)
                # col1, col2, col3 = st.columns(3)
                # col4, col5, col6 = st.columns(3)

                # with col2: 
                #     st.button("Show Experiments")

                # st.session_state.showExp = False

                if st.button("Show Previous Experiments", use_container_width=True):
                    st.session_state.showExp = True


                if st.session_state.showExp == True: 
                    st.set_page_config(layout="wide")
                    st.write(df_nodata_nocirc)

                    exp_index = st.number_input("Choose the index you want to display/review", min_value=0, step = 1)

                    if st.button(f"Display Experiment with index: {exp_index}"):
                        st.session_state.disp_exp = True

                    if st.session_state.disp_exp:
                        # base64_qc = base64.b64decode(df.iloc[exp_index]['experiment_circuit'])
                        # 1. Get the string from the dataframe
                        raw_data = df.iloc[exp_index]['experiment_circuit']

                        try:
                            # FIRST DECODE: Converts the outer Base64 layer
                            first_pass = base64.b64decode(raw_data)
                            
                            # Check if the result is still a string/text (Base64)
                            # If it starts with 'UUlT' (Base64 for QISK), we need to decode AGAIN
                            if first_pass.startswith(b'UUlT'):
                                # st.warning("Double-encoding detected. Performing second decode...")
                                final_binary = base64.b64decode(first_pass)
                            else:
                                final_binary = first_pass

                            # 2. Load into Qiskit
                            with io.BytesIO(final_binary) as f:
                                f.seek(0)
                                new_qc = qpy.load(f)[0]
                                
                            st.success("Circuit Loaded Successfully!")
                            # st.text(new_qc.draw())
                            st.pyplot(new_qc.draw("mpl"))

                        except Exception as e:
                            st.error(f"Error: {e}")
                            st.write(f"Header at fail: {first_pass[:10]}")

                        
                        raw_csv_data = df.iloc[exp_index]["experiment_data"]

                        try: 
                            # 1. First Decode
                            first_decode = base64.b64decode(raw_csv_data)
                            if first_decode.startswith(b'aXRl') or first_decode.startswith(b'bm9p'):
                                binary_csv = base64.b64decode(first_decode)
                            else:
                                binary_csv = first_decode


                            csv_buffer = io.BytesIO(binary_csv)
                            actual_df = pd.read_csv(csv_buffer)

                            if 'noise_type' in actual_df.columns:
                                st.write("### Experiment Results")
                                # QExperiment_NoiseInjection.display_results(actual_df) 

                            else:
                                st.error(f"Column 'noise_type' not found. Available: {actual_df.columns.tolist()}")

                        except Exception as e: 
                            st.error(f"Error: {e}")

                        if st.button("DONE!!!"):
                            st.session_state.showExp = False
                            st.session_state.disp_exp = False
                            st.rerun()




    # if show == True:
    #     with st.container(border = True, key = "green_container2"):
    #         st.html(f"<style>{home.css}</style>")
    #         exp_index = st.number_input("Choose the index you want to display/review", min_value=0, step = 1)
    #         exp = st.button(f"Display Experiment with index: {exp_index}")

    #         if exp == True: 
    #             qc = base64.b64decode(df.iloc(exp_index)['experiment_circuit'])
    #             qc = io.BytesIO(qc)
    #             with open("retrieved_circuit.qpy", "wb") as f:
    #                 f.write(qc.getbuffer())

                

    #             # new_qx = qpy.load(qc)[0]
    #             # print(new_qx)
                
    #             print()