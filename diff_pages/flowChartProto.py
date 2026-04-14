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
from q_prog_src import qiskit_circuit_general

# ============================================
# PAGE CONFIGURATION (must be first command)
# ============================================
st.set_page_config(page_title="Quantum Flow Builder", layout="wide", page_icon="✨")

# ============================================
# LUXURY DARK THEME + GLASSMORPHISM CSS
# ============================================
def inject_custom_css():
    st.markdown("""
    <style>
                
                

    /* Import modern sans-serif font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&family=Montserrat:wght@400;500;600;700&display=swap');
    
    /* Global override for Streamlit's native dark mode - maintain dark luxury feel */
    .stApp {
        background: radial-gradient(circle at 20% 30%, #106e3f, #cccaca);
    }
    
    /* Force all text to use luxury font family */
    html, body, div, span, p, h1, h2, h3, h4, h5, h6, label, button, input, select, textarea {
        font-family: 'Inter', 'Montserrat', sans-serif !important;
    }
    
    # /* Glassmorphism effect for columns - frosted glass with blur and thin gold border */
    # div[data-testid="stHorizontalBlock"] > div:nth-of-type(1),
    # div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) {
    #     background: rgba(18, 18, 24, 0.55) !important;
    #     backdrop-filter: blur(12px);
    #     -webkit-backdrop-filter: blur(12px);
    #     border-radius: 28px;
    #     border: 1px solid rgba(212, 175, 55, 0.25);
    #     box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    #     transition: all 0.3s ease;
    #     padding: 1.2rem;
    # }
                
        /* Glassmorphism for Column 1 (Canvas) */
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) {
        background: rgba(40, 30, 10, 0.4) !important; /* Gold tint background */
        backdrop-filter: blur(12px);
        border-radius: 28px;
        border: 1px solid rgba(212, 175, 55, 0.3); /* Gold border */
        # padding: 1.2rem;
    }
    
    /* Glassmorphism for Column 2 (Node Palette) */
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) {
        background: rgba(40, 30, 10, 0.3) !important; /* Gold tint background */
        backdrop-filter: blur(12px);
        border-radius: 28px;
        border: 1px solid rgba(212, 175, 55, 0.3); /* Gold border */
        # padding: 1.2rem;
    }
                
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(3) {
        background: rgba(40, 30, 10, 0.3) !important; /* Gold tint background */
        backdrop-filter: blur(12px);
        border-radius: 28px;
        border: 1px solid rgba(212, 175, 55, 0.3); /* Gold border */
        # padding: 1.2rem;
    }

    
    /* Hover effect for glass panels */
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(1):hover,
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(2):hover,
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(3):hover {
        border-color: rgba(0, 229, 255, 0.4);
        box-shadow: 0 12px 40px rgba(0, 229, 255, 0.08);
    }
    
    /* Premium pill-shaped buttons with glow effects */
    div[data-testid="stButton"] button {
        border-radius: 40px !important;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: all 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        border: none;
        # background: rgba(40, 30, 10, 0.4) !important; /* Gold tint background */
        backdrop-filter: blur(4px);
        color: #E0E0E0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        padding: 2rem 1.2rem;
        width: 100%;
    }
    
    div[data-testid="stButton"] button:hover {
        transform: translateY(-4px);
    }    
    div.st-key-btn_input button {
        background: linear-gradient(135deg, #0b2b5e, #1a4a8a) !important;
        color: white !important;
    }
    div.st-key-btn_backend_lux button {
        background: linear-gradient(135deg, #2a1e5a, #4a2e8a) !important;
        color: white !important;
    }
    
    div.st-key-btn_compress_lux button {
        background: linear-gradient(135deg, #aa6f20, #d4af37) !important;
        color: white !important;
    }
    
    div.st-key-btn_qucad_lux button {
        background: linear-gradient(135deg, #d4af37, #f5cb5c) !important;
    }
    
    div.st-key-btn_nocomp_lux button, div.st-key-btn_clear button {
        background: linear-gradient(135deg, #8b5a2b, #c97e3a) !important;
    }
    
    div.st-key-btn_qbound_lux button, div.st-key-btn_run button {
        background: linear-gradient(135deg, #1b6b4a, #2d9c6e) !important; /* emerald */
    }
    
    div.st-key-btn_simple_lux button {
        background: linear-gradient(135deg, #2c6e6e, #3fa0a0) !important; /* cyan-teal */
    }
    
    div.st-key-btn_transpile_lux button, div.st-key-btn_autoconnect button {
        background: linear-gradient(135deg, #aa4f2e, #dd7a4a) !important; /* sunset orange */
    }    
    /* Category expander styling - luxury clean */
    .streamlit-expanderHeader {
        font-size: 1.1rem;
        font-weight: 600;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 18px;
        color: #D4AF37 !important;
        border-left: 3px solid #D4AF37;
    }
    
    .streamlit-expanderContent {
        background: rgba(10, 10, 15, 0.4);
        border-radius: 20px;
        padding: 0.5rem;
    }
    
    /* Headers and subtitles in luxury gold/cyan */
    h1, h2, h3, h4, .stSubheader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #D4AF37 !important;
        font-weight: 600;
        letter-spacing: -0.2px;
    }
                
    
    
    
    .stSubheader {
        color: #00E5FF !important;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    /* Divider with gradient */
    hr {
        margin: 1rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #D4AF37, #00E5FF, transparent);
    }
    
    /* Custom scrollbar for containers */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(30,30,40,0.5);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #D4AF37;
        border-radius: 10px;
    }
    
    /* Label styling in property editor */
    .stSelectbox label, .stSlider label, .stRadio label, .stFileUploader label {
        color: #CCCCCC !important;
        font-weight: 500;
    }
    
    
    /* Info box styling */
    .stAlert {
        background: rgba(0, 229, 255, 0.1) !important;
        border-left: 3px solid #00E5FF !important;
        border-radius: 16px !important;
    }
    
    /* Canvas container specific */
    .stVerticalBlock {
        gap: 0.8rem;
    }
                
    div[data-testid="stElementContainer"] .st-key-btn_input button {
        background: linear-gradient(135deg, #aa6f20, #d4af37);
        color: white;
        border: none;
    }
    
    </style>
    """, unsafe_allow_html=True)

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
    "transpile": "linear-gradient(135deg, #aa4f2e, #dd7a4a)"      # sunset orange
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
        c2 = st.columns([1])[0]  # Single column for NoCompression
        with c2:
            if st.button("⚡ NoCompression", key="btn_nocomp_lux", use_container_width=True):
                add_unique_node("nocomp_node", "NoCompression", NODE_COLORS["nocomp"])

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
                mode = st.radio("Optimization Mode", ["Start Fresh", "Use Previous QNN"], horizontal=True)
                if mode == "Use Previous QNN":
                    st.success("Previous QNN weights will be reused.")
            
            elif "transpile_node" == node_id:
                st.session_state.opt_level = st.slider("Qiskit Optimization Level", 0, 3, 1, help="Higher = more aggressive transpilation")
                st.write(f"Optimization Level: {st.session_state.opt_level}")
            
            elif "qbound_node" == node_id:
                st.session_state.error_tolerance = st.slider("Error Tolerance", 0.01, 0.5, 0.05, step=0.01, help="Bound on allowed infidelity")
            
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
                
                # Backend connections to noise-aware nodes
                if backend_n:
                    if "qucad_node" in nodes_dict:
                        new_edges.append(StreamlitFlowEdge("backend-to-qucad", backend_n.id, "qucad_node", animated=True, label="Noise Profile", style={"stroke": "#00E5FF", "strokeDasharray": "5,5"}))
                    if "qbound_node" in nodes_dict:
                        new_edges.append(StreamlitFlowEdge("backend-to-qbound", backend_n.id, "qbound_node", animated=True, label="Error Data", style={"stroke": "#00E5FF", "strokeDasharray": "5,5"}))
                
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
                st.success(f"✅ Execution Complete! Fidelity Score: {st.session_state.fidelity_error_bound:.6f}")
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