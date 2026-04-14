import streamlit as st
import torch
import io
import numpy as np
import json
import time
from datetime import datetime
from qiskit import transpile

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
        time.sleep(5)
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
            # Logic for QuCAD from showcase
            noise_model, backend_ibm, target_props = QuCAD.get_noiseModel_andBackend_ondate()
            c_bar.progress(40, text="Getting QuCAD Training Data...")
            
            # Note: For fresh training logic, you can add state checks here
            final_theta, final_mask, stats = QuCAD.run_qucad_training_noisy(
                current_qc, noise_model, backend_ibm, iterations=10, lam=0.005, rho=500.0
            )
            qucad_bank = QuCAD.generate_qucad_lut(current_qc, backend_ibm)
            c_bar.progress(60, text="Generating Lookup Table ...")
            
            # Apply drift/multiplier logic
            # Using datetime.now() as default since flowchart date picker wasn't explicit
            target_date = datetime.now() 
            _, _, props_future = QuCAD.get_noiseModel_andBackend_ondate(target_date)
            multiplier = QuCAD.get_current_noise_multiplier(props_future, backend_ibm.properties())
            c_bar.progress(80, text="Applying Drift/Multiplier...")
            current_qc = QuCAD.deploy_qucad_model(current_qc, qucad_bank, multiplier)
            c_bar.progress(100, text="QuCAD Compression Finished")
        else:
            c_bar.progress(100, text="Compression Skipped")

        # --- PHASE 2: FIDELITY ---
        if "qbound_node" in nodes_present:
            f_bar.progress(50, text="Calculating QuBound...")
            # We use None for date to default to current backend noise
            fidelity_result, model_jit = test_QBound.call_QuBound(current_qc, provider, None)
            st.session_state.model = model_jit # Save for DB upload
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