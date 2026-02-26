import streamlit as st
from diff_pages import Home as home
from q_prog_src import qiskit_circuit_general, CompVQC, QBound
from qiskit import QuantumCircuit
from qiskit_ibm_runtime.fake_provider import FakeFez, FakeMarrakesh, FakeTorino
from datetime import datetime
import time
import requests
import torch
import io

def page():
    # --- 1. SESSION STATE INITIALIZATION ---
    if "verified" not in st.session_state:
        st.session_state.verified = False
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "experiment_finished" not in st.session_state:
        st.session_state.experiment_finished = False
    if "fidelity_error_bound" not in st.session_state: 
        st.session_state.fidelity_error_bound = 0.0
    if "model" not in st.session_state: 
        st.session_state.model = None

    st.html(f"<style>{home.css}</style>")

    with st.container(border=True, key='green_container'):
        st.header("Quantum Compression and Performance Prediction")

        # --- 2. UPLOAD FILE ---
        st.divider()
        st.session_state.uploaded_file = st.file_uploader(label="Upload your circuit qpy file Here:", type="qpy")

        if st.session_state.uploaded_file is not None:
            st.session_state.main_qc = qiskit_circuit_general.qasmFile_toCircuit(st.session_state.uploaded_file)
            st.pyplot(qiskit_circuit_general.display_circuit(st.session_state.main_qc))

        # --- 3. CONFIGURATION ---
        st.divider()
        backend_name = st.selectbox("Select Backends:", options=["ibm_fez", "ibm_marrakesh", "ibm_torino"])
        backends = {
            "ibm_fez": FakeFez(),          
            "ibm_marrakesh": FakeMarrakesh(), 
            "ibm_torino": FakeTorino() 
        }
        provider = backends[backend_name]

        col1, col2 = st.columns([2, 3], vertical_alignment="center")
        with col1:
            st.markdown("**COMPRESSION**")
        with col2:
            compression_selection = st.segmented_control(
                label="Compression Options",
                options=["CompressVQC", "QUCAD", "No Compression"],
                selection_mode="single",
                label_visibility="collapsed",
                default="No Compression"
            )
            if compression_selection == "No Compression":
                compression_selection = None

        col3, col4 = st.columns([2,3], vertical_alignment="center")
        with col3: 
            st.markdown("**FIDELITY ESTIMATION**")
        with col4: 
            fidelity_selection = st.segmented_control(
                label="Fidelity Options",
                options=["QuBound", "Simple Fidelity","Use_PRETrained Model"],
                selection_mode="single", 
                label_visibility="collapsed",
                default="Simple Fidelity"
            )
        
        if fidelity_selection == "Use_PRETrained Model":
            model_name = st.text_input("Enter your unique name for this QBound model:")
            if model_name:
                FASTAPI_URL = f"http://127.0.0.1:8000/load_QUbound?model_name={model_name}"
                try:
                    response = requests.get(FASTAPI_URL)
                    if response.status_code == 200:
                        model_bytes = io.BytesIO(response.content)
                        st.session_state.model = torch.jit.load(model_bytes)
                        st.success("Model retrieved")
                    else:
                        st.error("Failed to retrieve model from database.")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        
        col5, col6 = st.columns([2,3], vertical_alignment="center")
        with col5: 
            st.markdown("**IMPLEMENT NOISE MODEL**")
        with col6: 
            option = st.radio(
                label="noise_opt",
                options=["Yes","No Noise"],
                index=1,
                horizontal=True,
                label_visibility="collapsed",
            )

        date = None
        if option == "Yes":
            st.warning("You have selected YES to a noise model.")
            date_input = st.date_input("Select Date", value=datetime.now())
            date = datetime.combine(date_input, datetime.min.time())

        # --- 4. OPTIMIZATION ---
        optim_map = {
            "0: NO QISKIT OPTMIZATION": 0,
            "1: LIGHT OPTMIZATION; Basic gate folding": 1,
            "2: MEDIUM; Commutative analysis": 2,
            "3: HEAVY; Deep pulse-levl Optimization": 3
        }
        col7, col8 = st.columns([2,3], vertical_alignment="center")
        with col7: 
            st.markdown("**TRANSPILE OPTIMIZATION**")
        with col8:
            optmization_choice = st.selectbox("Select qiskit Optimization Level:", options=list(optim_map.keys()), label_visibility="hidden")
            optmization_level = optim_map[optmization_choice]

        # --- 5. VERIFICATION & SUBMISSION ---
        st.divider()
        if st.button("VERIFY Request"):
            st.session_state.verified = True

        if st.session_state.verified: 
            chosen_modifications = {
                "Backend": backend_name,
                "Compression": compression_selection,
                "Fidelity": fidelity_selection,
                "Noise Model": option,
                "Noise Date": date, 
                "Transpile Optimization Level": optmization_level
            }
            st.write(chosen_modifications)
            
            if st.button("SUBMIT Request"):
                st.session_state.submitted = True
                st.session_state.experiment_finished = False

        # --- 6. PERFORMING EXPERIMENT ---
        if st.session_state.submitted and st.session_state.verified:
            
            # This container stays visible after the experiment is finished
            with st.container(border=True):
                st.markdown("### ⚙️ Experiment Status")
                
                # Placeholder for progress bars so they stay on screen
                compress_bar = st.progress(0, text="Compression Phase")
                fidelity_bar = st.progress(0, text="Fidelity Phase")
                transpile_bar = st.progress(0, text="Final Transpilation")

                if not st.session_state.experiment_finished:
                    # --- EXECUTION LOGIC ---
                    # 1. Compression
                    if compression_selection == "CompressVQC":
                        active_qc = st.session_state.main_qc
                        lut = CompVQC.get_LUT(active_qc, provider)
                        if not lut:
                            st.error("No parameterizable gates found!")
                            st.stop()
                        
                        compress_bar.progress(50, "Constructing Quadratic Problem...")
                        qp = CompVQC.quadraticProgram_luttoqp(active_qc, lut)
                        result = CompVQC.admmOptimizedCompVQC(qp)
                        st.session_state.main_qc = CompVQC.resultsCompressVQC(result, active_qc)
                        compress_bar.progress(100, "Compression Complete")
                    else:
                        compress_bar.progress(100, "No Compression Requested")

                    # 2. Fidelity
                    if fidelity_selection == "Simple Fidelity":
                        st.session_state.fidelity_error_bound = qiskit_circuit_general.simpleFidelityEstimator(st.session_state.main_qc)
                        fidelity_bar.progress(100, text=f"Fidelity calculated")
                    elif fidelity_selection == "QuBound":
                        st.session_state.fidelity_error_bound, st.session_state.model = QBound.call_QuBound(st.session_state.main_qc, provider, date)
                        fidelity_bar.progress(100, text=f"QBound finished")
                    else:
                        fidelity_bar.progress(100, text="Fidelity Step Skipped")

                    # 3. Transpile
                    st.session_state.main_qc = qiskit_circuit_general.transpile_optim(st.session_state.main_qc, backend_name, optmization_level)
                    transpile_bar.progress(100, text="Transpilation Complete")
                    
                    st.session_state.experiment_finished = True
                
                else:
                    # Logic to keep bars at 100% when experiment is already done
                    compress_bar.progress(100, text="Compression Phase: Finished")
                    fidelity_bar.progress(100, text="Fidelity Phase: Finished")
                    transpile_bar.progress(100, text="Final Transpilation: Finished")

            # --- 7. DISPLAY RESULTS ---
            if st.session_state.experiment_finished:
                st.success(f"Analysis Complete! Your Fidelity score is: {st.session_state.fidelity_error_bound}")
                st.pyplot(qiskit_circuit_general.display_circuit(st.session_state.main_qc))

                # Database Upload Section
                st.divider()
                st.markdown("### 📤 Database Management")
                
                with st.form("db_upload_form"):
                    model_name_input = st.text_input("Assign a unique name to this QBound model:")
                    upload_btn = st.form_submit_button("Upload Model to MongoDB")

                    if upload_btn:
                        if not model_name_input:
                            st.error("Please enter a model name.")
                        elif st.session_state.model is None:
                            st.error("No JIT model found.")
                        else:
                            try:
                                # Logic for JIT conversion and upload
                                buffer = io.BytesIO()
                                torch.jit.save(st.session_state.model, buffer)
                                buffer.seek(0)

                                payload = {"username": "user", "model_name": model_name_input}
                                files = {"file": (f"{model_name_input}.pt", buffer, "application/octet-stream")}

                                with st.spinner("Uploading..."):
                                    res = requests.post("http://127.0.0.1:8000/save_QUbound", data=payload, files=files)
                                
                                if res.status_code == 200:
                                    st.success(f"Model '{model_name_input}' saved successfully!")
                                else:
                                    st.error(f"Upload failed: {res.text}")
                            except Exception as e:
                                st.error(f"Error during upload: {e}")

                if st.button("Start New Experiment"):
                    for key in ["submitted", "verified", "experiment_finished", "model", "fidelity_error_bound"]:
                        st.session_state[key] = False
                    st.rerun()

if __name__ == "__main__":
    page()