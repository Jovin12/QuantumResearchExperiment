import streamlit as st
import torch
import io
import numpy as np
import json
import time
from datetime import datetime
from qiskit import transpile
import requests

# Import your quantum backend logic
from q_prog_src import test_QBound, qiskit_circuit_general, CompVQC, QuCAD
from qiskit_ibm_runtime.fake_provider import FakeFez, FakeMarrakesh, FakeTorino

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)): return float(obj)
        if isinstance(obj, (np.int32, np.int64)): return int(obj)
        return super(NumpyEncoder, self).default(obj)

def execute(progress_container):
    """
    Translates the Flowchart UI state into the execution logic 
    found in the original QExperiment_showcase submit button.
    progress_container: Streamlit container to display progress bars
    """
    st.set_page_config(layout = "wide")
    
    # 1. DATA VALIDATION: Ensure we have nodes and a circuit
    if 'flow_state' not in st.session_state or not st.session_state.flow_state.nodes:
        st.error("Your canvas is empty! Add nodes to the workflow.")
        return
    
    uploaded_file = st.session_state.get('uploaded_file') or st.session_state.get('circuit_upload')
    if uploaded_file is not None:
        current_qc = qiskit_circuit_general.qasmFile_toCircuit(uploaded_file)
        st.session_state.main_qc = current_qc
    else:
        st.error("Please select the Circuit Node and upload a .qpy file first.")
        # st.session_state.should_execute = False
        # time.sleep(5)
        return

    # Map nodes by ID for easy lookup
    nodes_present = {node.id for node in st.session_state.flow_state.nodes}
    
    # 2. BACKEND SETUP
    # Pulls backend_name directly from session state set in flowChartProto.py
    backend_name = st.session_state.get('backend_name', 'ibm_fez')
    backends = {
        "ibm_fez": FakeFez(),          
        "ibm_marrakesh": FakeMarrakesh(), 
        "ibm_torino": FakeTorino() 
    }
    provider = backends.get(backend_name, FakeFez())

    # Initialize working variables
    fidelity_result = 0.0

    # 3. EXECUTION VISUALS (Progress Bars) - use persistent container passed in
    with progress_container.container(border=True):
        st.markdown(f"### 🚀 Running Workflow on **{backend_name}**")
        c_bar = st.progress(0, text="Compression Phase")
        f_bar = st.progress(0, text="Fidelity Phase")
        t_bar = st.progress(0, text="Transpilation Phase")

        # --- PHASE 1: COMPRESSION ---
        if "compress_node" in nodes_present:
            c_bar.progress(20, text="Running CompressVQC...")
            lut = CompVQC.get_LUT(current_qc, provider)
            if lut:
                qp = CompVQC.quadraticProgram_luttoqp(current_qc, lut)
                result = CompVQC.admmOptimizedCompVQC(qp)
                current_qc = CompVQC.resultsCompressVQC(result, current_qc)
                c_bar.progress(100, text="CompressVQC Finished")
            else:
                st.warning("CompressVQC: No parameterizable gates found.")
        



        elif "qucad_node" in nodes_present:
            c_bar.progress(20, text="Initializing QuCAD...")

            if not st.session_state.get('qucad_bank', False):
                
                # Logic for QuCAD from showcase
                noise_model, backend_ibm, target_props = QuCAD.get_noiseModel_andBackend_ondate()
                c_bar.progress(40, text="Getting QuCAD Training Data...")
                
                # Note: For fresh training logic, you can add state checks here
                final_theta, final_mask, stats = QuCAD.run_qucad_training_noisy(
                    current_qc, noise_model, backend_ibm, iterations=10, lam=0.005, rho=500.0
                )
                st.session_state.qucad_bank = QuCAD.generate_qucad_lut(current_qc, backend_ibm)
                c_bar.progress(60, text="Generating Lookup Table ...")
                
                # NEW: Save the model to backend if it's a fresh training
                model_name = st.session_state.get('model_name')
                username = st.session_state.get('username', 'anonymous')  # You'll need to set this from login
                
                if model_name and not st.session_state.get('qucad_model_saved', False):
                    try:
                        qucad_bank_json = json.dumps(st.session_state.qucad_bank, cls=NumpyEncoder)
                        import requests
                        response = requests.post(
                            "http://127.0.0.1:8000/save_QuCAD",
                            data={
                                "username": username,
                                "model_name": model_name,
                                "qucad_bank": qucad_bank_json
                            }
                        )
                        if response.status_code == 200:
                            st.session_state.qucad_model_saved = True
                            st.success(f"✅ QuCAD model '{model_name}' saved to database")
                        else:
                            st.warning(f"⚠️ Could not save model: {response.text}")
                    except Exception as e:
                        st.warning(f"⚠️ Could not save model to database: {e}")



            
    # Apply drift/multiplier logic...
        # --- PHASE 2: FIDELITY ---
        if "qbound_node" in nodes_present:
            f_bar.progress(50, text="Calculating QuBound...")
            # We use None for date to default to current backend noise
            st.write(st.session_state.get('qbound_model', None))
            qbound_result = test_QBound.call_QuBound(current_qc, provider, model= st.session_state.get('qbound_model', None))



            if qbound_result is None:
                st.error("❌ QuBound failed: Authentication error. Please check your IBM Quantum token.")
                f_bar.progress(100, text="QuBound Failed")
                
            if st.session_state.get('qbound_model', None) is not None and qbound_result is not None: 
                st.info(" No Upload: Using existing ")
                fidelity_result, model_jit = qbound_result
            else:
                fidelity_result, model_jit = qbound_result
                st.session_state.qbound_model = model_jit # Save for DB upload

                if st.session_state.get('qbound_model', None) is not None: 
                    try:
                        # Logic for JIT conversion and upload
                        buffer = io.BytesIO()
                        # print(st.session_state.qbound_model)
                        # # torch.jit.save(st.session_state.qbound_model, buffer)
                        # torch.save(st.session_state.qbound_model, buffer)

                        print(st.session_state.qbound_model)
        
                        # Convert to TorchScript using tracing
                        model = st.session_state.qbound_model
                        model.eval()
                        
                        # Create a dummy input with the correct shape
                        # Based on your model: LSTM(12, 32) expects input shape (batch, seq_len, 12)
                        dummy_input = torch.randn(1, 5, 12)  # batch=1, sequence_length=5, input_features=12
                        
                        # Trace the model
                        traced_model = torch.jit.trace(model, dummy_input)
                        
                        # Save the traced model
                        torch.jit.save(traced_model, buffer)
                        buffer.seek(0)


                        payload = {"username": "user", "model_name": st.session_state.get('model_name', 'noNameqBound')}
                        files = {"file": (f"{st.session_state.get('model_name', 'noNameqBound')}.pt", buffer, "application/octet-stream")}

                        with st.spinner("Uploading..."):
                            import requests
                            res = requests.post("http://127.0.0.1:8000/save_QUbound", data=payload, files=files)
                        
                        if res.status_code == 200:
                            st.success(f"Model '{st.session_state.get('model_name', 'noNameqBound')}' saved successfully!")
                        else:
                            st.error(f"Upload failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error during upload: {e}")
                


                f_bar.progress(100, text="QuBound Finished")

                






                
            
        elif "simple_node" in nodes_present:
            f_bar.progress(50, text="Calculating Simple Fidelity...")
            try:
                fidelity_result = qiskit_circuit_general.simpleFidelityEstimator(current_qc)
                f_bar.progress(100, text="Fidelity Calculated")
            except:
                f_bar.progress(100, text="Simple Fidelity failed (Parameterized circuit)")
        else:
            f_bar.progress(100, text="Fidelity Skipped")

        # --- PHASE 3: TRANSPILE ---
        if "transpile_node" in nodes_present:
            # Get opt_level from slider in flowChartProto
            level = st.session_state.get('opt_level', 1)
            t_bar.progress(50, text=f"Transpiling (Level {level})...")
            current_qc = qiskit_circuit_general.transpile_optim(current_qc, provider,level)
            t_bar.progress(100, text="Transpilation Finished")
        else:
            t_bar.progress(100, text="Transpilation Skipped")

    
    # st.session_state.clear()
    # Store results back into session state for database forms
    st.session_state.fidelity_error_bound = fidelity_result
    st.session_state.main_qc = current_qc
    st.session_state.execution_complete = True