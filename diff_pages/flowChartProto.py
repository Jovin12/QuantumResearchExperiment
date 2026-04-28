import sys
from pathlib import Path
import time as t

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from q_prog_src.execute_workflow import execute
from q_prog_src import test_QBound
from q_prog_src import qiskit_circuit_general
import requests, json
from css_page import inject_custom_css
import torch 
import io

# ============================================
# PAGE CONFIGURATION (must be first command)
# ============================================
st.set_page_config(page_title="Quantum Flow Builder", layout="wide", page_icon="✨")

# ============================================
# LUXURY DARK THEME + GLASSMORPHISM CSS
# ============================================
inject_custom_css()

# ============================================
# QUANTUM NODES WITH GRADIENTS / GLOWING BORDERS
# ============================================
NODE_COLORS = {
    "input": "linear-gradient(135deg, #0b2b5e, #1a4a8a)",       # deep quantum blue
    "backend": "linear-gradient(135deg, #2a1e5a, #4a2e8a)",     # royal purple
    "compress": "linear-gradient(135deg, #aa6f20, #d4af37)",     # gold gradient
    "qucad": "linear-gradient(135deg, #d4af37, #f5cb5c)",        # soft gold
    "nocomp": "linear-gradient(135deg, #8b5a2b, #c97e3a)",       # amber
    "qbound": "linear-gradient(135deg, #1b6b4a, #2d9c6e)",       # emerald
    "simple": "linear-gradient(135deg, #2c6e6e, #3fa0a0)",       # cyan-teal
    "transpile": "linear-gradient(135deg, #aa4f2e, #dd7a4a)",     # sunset orange
    "qushot": "linear-gradient(135deg, #7a1e5a, #c4468a)"         # rose-magenta
}



def get_node_style(node_type, color_gradient):
    """Return a style dict with glowing border and gradient background"""
    return {
        "background": color_gradient,
        "color": "#ffffff",
        "border": "1px solid rgba(0, 229, 255, 0.5)",
        "borderRadius": "16px",
        "boxShadow": "0 0 8px rgba(0, 229, 255, 0.3), 0 4px 12px rgba(0,0,0,0.3)",
        "fontWeight": "600",
        "padding": "8px 16px",
        "backdropFilter": "blur(2px)",
        "transition": "all 0.2s"
    }

def flow_page():
    # Inject luxury dark mode CSS with glassmorphism
    inject_custom_css()
    
    # Initialize Session State with robust persistence
    if 'flow_state' not in st.session_state:
        st.session_state.flow_state = StreamlitFlowState([], [])
    if 'backend_name' not in st.session_state:
        st.session_state.backend_name = "ibm_fez"
    if 'should_execute' not in st.session_state:
        st.session_state.should_execute = False
    if 'execution_complete' not in st.session_state:
        st.session_state.execution_complete = False
    if 'model_name' not in st.session_state: 
        st.session_state.model_name = None
    # Add this line with other initializations
    if 'qbound_model_name' not in st.session_state:
        st.session_state.qbound_model_name = None
    if 'qbound_model' not in st.session_state:
        st.session_state.qbound_model = None
    
    # Layout: Flow Canvas (col1) and Node Palette (col2)
    col1, col2 = st.columns([4, 1.75])
    
    # ============================================
    # RIGHT COLUMN: NODE PALETTE (Glass + Expanders)
    # ============================================
    with col2:
        st.markdown("<h2 style='text-align:center; margin-bottom:0;'>✨ QUANTUM NODES</h2>", unsafe_allow_html=True)
        # st.markdown("<p style='text-align:center; color:#aaa; font-size:0.8rem;'>Drag & drop to canvas</p>", unsafe_allow_html=True)
        st.divider()
        
        # Helper function to prevent duplicates by checking ID, but with quantum node styling
        def add_unique_node(node_id, content, color_gradient, node_type='default', label=None):
            # Remove existing node with same ID to avoid duplicates
            st.session_state.flow_state.nodes = [n for n in st.session_state.flow_state.nodes if n.id != node_id]

            # print(color_gradient)
            
            # Create node with quantum gradient style
            new_node = StreamlitFlowNode(
                id=node_id,
                pos=(50, 50),
                data={'content': content},
                node_type=node_type,
                label=label if label else content,
                draggable=True,
                style=get_node_style(node_type, color_gradient),
                selectable=True,
                deletable=True,
            )
            st.session_state.flow_state.nodes.append(new_node)
        
        # ---- INPUT NODES SECTION ----
        st.markdown("**⚛️ INPUT QUANTUM STATES**")
        
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("🔮 Circuit Node", key="btn_input", use_container_width=True):
                add_unique_node("input_node", "Quantum Circuit", NODE_COLORS["input"], "input", "CIRCUIT")
        with c2:
            if st.button("🎛️ Backend Node", key="btn_backend_lux", use_container_width=True):
                add_unique_node("backend_node", "Quantum Backend", NODE_COLORS["backend"], "input", "BACKEND")
        
        st.divider()
        # ---- COMPRESSION SECTION ----
        st.markdown("**🌀 COMPRESSION & OPTIMIZATION**")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Compress VQC", key="btn_compress_lux", use_container_width=True):
                add_unique_node("compress_node", "CompressVQC", NODE_COLORS["compress"])
        with c2:
            if st.button("QuCAD", key="btn_qucad_lux", use_container_width=True):
                add_unique_node("qucad_node", "QuCAD", NODE_COLORS["qucad"])
        # c2 = st.columns([1])[0]  # Single column for NoCompression
        # with c2:
        #     if st.button("⚡ NoCompression", key="btn_nocomp_lux", use_container_width=True):
        #         add_unique_node("nocomp_node", "NoCompression", NODE_COLORS["nocomp"])

        st.divider()
        # ---- FIDELITY SECTION ----
        st.markdown("**📊 FIDELITY & ERROR BOUNDS**")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("QuBound", key="btn_qbound_lux", use_container_width=True):
                add_unique_node("qbound_node", "QuBound", NODE_COLORS["qbound"])
        with c2:
            if st.button("Simple Fidelity", key="btn_simple_lux", use_container_width=True):
                add_unique_node("simple_node", "SimpleFid", NODE_COLORS["simple"])
        
        st.divider()
        # ---- TRANSPILATION SECTION ----
        st.markdown("**⚙️ TRANSPILATION ENGINE**")

        c1 = st.columns([1])[0]  # Single column for Transpiler
        with c1:
            if st.button("🚀 Transpile Node", key="btn_transpile_lux", use_container_width=True):
                add_unique_node("transpile_node", "Transpiler", NODE_COLORS["transpile"])

        st.divider()
        # ---- SHOT RECOMMENDATION SECTION ----
        st.markdown("**🎯 SHOT RECOMMENDATION**")

        c1 = st.columns([1])[0]
        with c1:
            if st.button("Qushot", key="btn_qushot_lux", use_container_width=True):
                add_unique_node("qushot_node", "Qushot", NODE_COLORS["qushot"])

        st.divider()
        # st.caption("✨ Quantum nodes glow with electric cyan borders")
    
    # ============================================
    # LEFT COLUMN: FLOW CANVAS (Glass)
    # ============================================
    with col1:
        st.markdown("<h2 style='margin-top:0;'>🌌 QUANTUM FLOW CANVAS</h2>", unsafe_allow_html=True)
        
        # Render the interactive flow with full features
        flow_state = streamlit_flow(
            'quantum_flow_lux',
            state=st.session_state.flow_state,
            height=550,
            fit_view=True,
            show_controls=True,
            allow_new_edges=True,
            animate_new_edges=True,
            enable_node_menu=True,
            enable_edge_menu=True,
            get_node_on_click=True,
            # background_color="#0a0a12",
            # min_zoom=0.5,
            # max_zoom=1.5,
        )
        
        # CRITICAL: Persist state after any canvas interaction
        if flow_state is not None:
            st.session_state.flow_state = flow_state
        
        # --- Node Property Editor (Dynamic based on selected node) ---
        if st.session_state.flow_state.selected_id:
            node_id = st.session_state.flow_state.selected_id
            st.divider()
            st.markdown(f"<h3 style='color:#D4AF37;'>⚙️ {node_id.upper()} CONFIGURATION</h3>", unsafe_allow_html=True)
            
            if "input_node" == node_id:    
                st.session_state.uploaded_file = st.file_uploader("Upload Quantum Circuit (.qpy)", type="qpy", key="circuit_upload")

                st.caption("Accepts QPY format from Qiskit")
            
            elif "backend_node" == node_id:
                backend = st.selectbox("Select Target Quantum Backend:", 
                                       ["ibm_fez", "ibm_marrakesh", "ibm_torino", "ibm_brisbane"],
                                       index=["ibm_fez", "ibm_marrakesh", "ibm_torino", "ibm_brisbane"].index(st.session_state.backend_name))
                st.session_state.backend_name = backend
                st.info("🔗 Backend noise profiles are available for QuCAD and QuBound")


            
            elif "qucad_node" == node_id:
                st.info("🌀 QuCAD leverages backend noise for adaptive compression.")
                
                # 1. Wrap the inputs in a form to stop the "typing" refresh
                with st.form(key="qucad_search_form"):
                    mode = st.radio("Optimization Mode", ["Start Fresh", "Use Previous QNN"], horizontal=True)
                    
                    # Use a default value from session state to keep it persistent
                    model_input = st.text_input(
                        "Enter your unique name for this QuCAD model:", 
                        value=st.session_state.get('model_name', '') or ""
                    )
                    
                    # Every form needs a submit button
                    submit_button = st.form_submit_button(label="🔍 Load Model")

                # 2. Logic only runs when the button is pressed
                if submit_button:
                    if mode == "Use Previous QNN":
                        if model_input:
                            st.session_state.model_name = model_input
                            FASTAPI_URL = f"http://127.0.0.1:8000/load_QuCAD?model_name={model_input}"
                            try:
                                with st.spinner("Fetching model..."):
                                    response = requests.get(FASTAPI_URL)
                                    if response.status_code == 200:
                                        # The backend returns a JSON object directly
                                        qucad_bank_data = response.json()
                                        
                                        # The backend returns the qucad_bank as a string that needs parsing
                                        # OR it returns a dict - check the type
                                        if isinstance(qucad_bank_data, str):
                                            qucad_bank_data = json.loads(qucad_bank_data)
                                        
                                        st.session_state.qucad_bank = qucad_bank_data
                                        st.success(f"✅ Model '{model_input}' retrieved successfully")
                                    else:
                                        st.error(f"❌ Failed to retrieve model. Status code: {response.status_code}")
                                        if response.status_code == 404:
                                            st.warning(f"Model '{model_input}' not found in database. Try a different name or select 'Start Fresh'.")
                            except requests.exceptions.ConnectionError:
                                st.error("📡 Cannot connect to backend server. Make sure FastAPI is running on http://127.0.0.1:8000")
                            except json.JSONDecodeError as e:
                                st.error(f"❌ Error parsing model data: {e}")
                            except Exception as e:
                                st.error(f"❌ Unexpected error: {e}")
                        else:
                            st.warning("Please enter a model name.")
                    else:  # Start Fresh mode
                        st.info("Optimization set to Start Fresh. A new model will be created after execution.")
                        # Clear any existing model name to avoid confusion
                        if 'model_name' in st.session_state:
                            st.session_state.model_name = None
                        if 'qucad_bank' in st.session_state:
                            st.session_state.qucad_bank = None





            
            elif "transpile_node" == node_id:
                st.session_state.opt_level = st.slider("Qiskit Optimization Level", 0, 3, 1, help="Higher = more aggressive transpilation")
                st.write(f"Optimization Level: {st.session_state.opt_level}")
            





            elif "qbound_node" == node_id:
                # st.session_state.error_tolerance = st.slider("Error Tolerance", 0.01, 0.5, 0.05, step=0.01, help="Bound on allowed infidelity")
                # 1. Wrap the inputs in a form to stop the "typing" refresh
                with st.form(key="qucad_search_form"):
                    mode = st.radio("Optimization Mode", ["Start Fresh", "Use Previous QuBound Model"], horizontal=True)
                    
                    # Use a default value from session state to keep it persistent
                    model_input = st.text_input(
                        "Enter your unique name for this QuBound model:", 
                        value=st.session_state.get('model_name', '') or ""
                    )
                    
                    # Every form needs a submit button
                    submit_button = st.form_submit_button(label="🔍 Load Model")
                
                # res = requests.post("http://127.0.0.1:8000/save_QUbound", data=payload, files=files)
                # FASTAPI_URL = f"http://127.0.0.1:8000/load_QUbound?model_name={model_name}"

                if submit_button: 
                    if mode == "Use Previous QuBound Model":
                        if model_input: 
                            st.session_state.q_bound_model_name = model_input
                            FASTAPI_URL = f"http://127.0.0.1:8000/load_QUbound?model_name={st.session_state.q_bound_model_name}"

                            try:
                                with st.spinner("Fetching model..."):
                                    response = requests.get(FASTAPI_URL)
                                    if response.status_code == 200:
                                        model_bytes = io.BytesIO(response.content)
                                        st.session_state.qbound_model = torch.jit.load(model_bytes)
                                        st.success("Model retrieved")
                                    else:
                                        st.error("Failed to retrieve model from database.")
                            except Exception as e:
                                st.error(f"Connection error: {e}")
                        else:
                            st.warning("Please enter a model name. ")
                    else: 
                        st.info("Optimization set to Start Fresh. A new model will be created after execution.")
                        # Clear any existing model name to avoid confusion
                        if 'model_name' in st.session_state:
                            st.session_state.model_name = None
                        if 'qbound_model' in st.session_state:
                            st.session_state.qbound_model = None





                






            
            elif "qushot_node" == node_id:
                st.info("🎯 Qushot recommends how many shots your circuit needs to reach a target fidelity.")

                # Discover bundled noise JSONs from qushot_internals/data/noise_json/
                _NOISE_DIR = Path(__file__).parent.parent / "q_prog_src" / "qushot_internals" / "data" / "noise_json"
                bundled_jsons = sorted([p.name for p in _NOISE_DIR.glob("*.json")]) if _NOISE_DIR.exists() else []

                CUSTOM_OPTION = "📤 Upload custom JSON..."
                PLACEHOLDER = "— Select a noise snapshot —"
                choices = [PLACEHOLDER] + bundled_jsons + [CUSTOM_OPTION]

                selected = st.selectbox(
                    "Noise snapshot",
                    choices,
                    index=0,
                    help="Pick a bundled IBM noise snapshot or upload your own.",
                )

                if selected == CUSTOM_OPTION:
                    uploaded = st.file_uploader(
                        "Upload noise JSON", type="json", key="qushot_custom_noise_upload",
                        help="JSON in the Qshot dataset noise snapshot format.",
                    )
                    if uploaded is not None:
                        try:
                            noise_dict = json.load(uploaded)
                            st.session_state.qushot_noise_json = noise_dict
                            st.success(f"✅ Loaded custom noise JSON ({len(uploaded.getvalue())} bytes).")
                        except json.JSONDecodeError as e:
                            st.error(f"❌ Invalid JSON: {e}")
                            st.session_state.qushot_noise_json = None
                elif selected != PLACEHOLDER:
                    st.session_state.qushot_noise_json = str(_NOISE_DIR / selected)
                    st.caption(f"Using bundled: `{selected}`")
                else:
                    st.session_state.qushot_noise_json = None

                alpha = st.slider(
                    "Target fidelity fraction (α)", 0.50, 0.95,
                    value=float(st.session_state.get('qushot_alpha', 0.95)), step=0.01,
                    help="Recommend shots needed to reach α × converged fidelity.",
                )
                st.session_state.qushot_alpha = alpha

            elif "compress_node" == node_id:
                st.checkbox("Preserve original gate structure", value=True)
        
        # --- Action Buttons for Flow Management (Luxury Pill Style)---
        st.divider()
        act_c1, act_c2, act_c3,act_c4 = st.columns([1, 1, 1, 0.5])
        
        # Get current nodes dictionary for auto-connect logic
        nodes_dict = {n.id: n for n in st.session_state.flow_state.nodes}
        
        with act_c1:
            if st.button("✨ AUTOCONNECT", use_container_width=True, help="Intelligently connect quantum workflow nodes", key = "btn_autoconnect"):
                new_edges = []
                
                # Identify key node categories
                input_n = nodes_dict.get("input_node")
                backend_n = nodes_dict.get("backend_node")
                comp_n = next((nodes_dict[i] for i in ["compress_node", "qucad_node", "nocomp_node"] if i in nodes_dict), None)
                fid_n = next((nodes_dict[i] for i in ["qbound_node", "simple_node"] if i in nodes_dict), None)
                transpile_n = nodes_dict.get("transpile_node")
                qushot_n = nodes_dict.get("qushot_node")

                # Build main quantum pipeline chain
                if input_n:
                    current_source = input_n.id
                    if comp_n:
                        new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{comp_n.id}", current_source, comp_n.id, animated=True, style={"stroke": "#00E5FF", "strokeWidth": 2}))
                        current_source = comp_n.id
                    if fid_n:
                        new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{fid_n.id}", current_source, fid_n.id, animated=True, style={"stroke": "#D4AF37", "strokeWidth": 2}))
                        current_source = fid_n.id
                    if transpile_n:
                        new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{transpile_n.id}", current_source, transpile_n.id, animated=True, style={"stroke": "#00E5FF", "strokeWidth": 2}))
                        current_source = transpile_n.id
                    if qushot_n:
                        new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{qushot_n.id}", current_source, qushot_n.id, animated=True, style={"stroke": "#FF6EC7", "strokeWidth": 2}))
                        current_source = qushot_n.id

                # Backend connections to noise-aware nodes
                if backend_n:
                    if "qucad_node" in nodes_dict:
                        new_edges.append(StreamlitFlowEdge("backend-to-qucad", backend_n.id, "qucad_node", animated=True, label="Noise Profile", style={"stroke": "#00E5FF", "strokeDasharray": "5,5"}))
                    if "qbound_node" in nodes_dict:
                        new_edges.append(StreamlitFlowEdge("backend-to-qbound", backend_n.id, "qbound_node", animated=True, label="Noise Profile", style={"stroke": "#00E5FF", "strokeDasharray": "5,5"}))
                    if "qushot_node" in nodes_dict:
                        new_edges.append(StreamlitFlowEdge("backend-to-qushot", backend_n.id, "qushot_node", animated=True, label="Noise Profile", style={"stroke": "#00E5FF", "strokeDasharray": "5,5"}))
                
                st.session_state.flow_state.edges = new_edges
                st.rerun()
        
        with act_c2:
            if st.button("🗑️ CLEAR CANVAS", use_container_width=True, help="Remove all nodes and edges", key = 'btn_clear'):
                st.session_state.flow_state = StreamlitFlowState([], [])
                st.session_state.clear()
                st.rerun()
        
        with act_c3:
            if act_c3.button(" 🏃 RUN SIMULATION", use_container_width = True, help = 'Run your flow chart with Backend', key = 'btn_run'):
                st.session_state.should_execute = True
        
        # Create persistent containers for results
        progress_placeholder = st.empty()
        results_placeholder = st.empty()
        
        # Only execute if flag is set and not yet complete
        if st.session_state.get('should_execute', False) and not st.session_state.get('execution_complete', False):
            st.session_state.execution_complete = False
            execute(progress_placeholder)
        
        # Display results after execution completes
        if st.session_state.get('execution_complete', False):
            with results_placeholder.container():
                st.divider()
                # st.success(f"✅ Execution Complete! Fidelity Score: {st.session_state.fidelity_error_bound:.6f}")
                # st.write(st.session_state.fidelity_error_bound)
                st.write(test_QBound.interpret_qubound_results(st.session_state.fidelity_error_bound))

                # --- Qushot results ---
                qushot_result = st.session_state.get('qushot_result')
                if qushot_result is not None:
                    st.divider()
                    st.subheader("🎯 Qushot Shot-Count Recommendation")
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Recommended Shots", qushot_result.get('recommended_shots', '—'))
                    pf = qushot_result.get('predicted_fidelity')
                    ps = qushot_result.get('predicted_std')
                    if pf is not None:
                        col_b.metric(
                            "Predicted Fidelity",
                            f"{pf:.4f}",
                            delta=f"±{ps:.4f}" if ps is not None else None,
                            delta_color="off",
                        )
                    col_c.metric("Method", qushot_result.get('method', '—'))

                    fit = qushot_result.get('fit') or {}
                    alpha = fit.get('alpha')
                    target = fit.get('target')
                    f_conv = fit.get('F_inf')
                    if alpha is not None and target is not None:
                        f_conv_str = f"{f_conv:.4f}" if isinstance(f_conv, float) else str(f_conv)
                        st.caption(
                            f"Target: α={alpha} × converged F "
                            f"(F_inf={f_conv_str}) = {target:.4f}"
                        )
                    cl = qushot_result.get('cluster_label')
                    tier = qushot_result.get('tier')
                    nmatch = qushot_result.get('n_matched')
                    if cl is not None:
                        st.caption(f"Cluster: {cl} · Tier: {tier} · PF-matched neighbors: {nmatch}")

                    with st.expander("Full recommendation details"):
                        st.json(qushot_result)

                st.subheader("Circuit Diagram")
                try:
                    fig = qiskit_circuit_general.display_circuit(st.session_state.main_qc)
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Could not display circuit: {e}")

                # Reset flags for next run
                if st.button("🔄 Run Again", key="btn_run_again"):
                    st.session_state.should_execute = False
                    st.session_state.execution_complete = False
                    st.rerun()
        # Optional: display backend info for status
        st.caption(f"🎛️ Active Quantum Backend: **{st.session_state.backend_name}** | Nodes: {len(st.session_state.flow_state.nodes)} | Edges: {len(st.session_state.flow_state.edges)}")

# ============================================
# ENTRY POINT
# ============================================
if __name__ == "__main__":
    flow_page()