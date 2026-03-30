import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState

def flow_page():
    # Injecting CSS for styling
    st.markdown("""
    <style>

    /* General button styling */
    div[data-testid="stButton"] button {
        border-radius: 8px;
        font-weight: 600;
        width: 150px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Input Nodes */
    div[data-testid="stVerticalBlock"] > div:nth-of-type(1) button {
        background-color: #4a86e8; color: black;
    }
    div[data-testid="stVerticalBlock"] > div:nth-of-type(2) button {
        background-color: #4a86e8; color: white;
    }

    /* Compression Nodes */
    div[data-testid="stVerticalBlock"] > div:nth-of-type(4) button {
        background-color: #50C878; color: black;
    }
    div[data-testid="stVerticalBlock"] > div:nth-of-type(5) button {
        background-color: #FFD700; color: black;
    }
    div[data-testid="stVerticalBlock"] > div:nth-of-type(6) button {
        background-color: #FF7F50; color: white;
    }

    /* Fidelity Nodes */
    div[data-testid="stVerticalBlock"] > div:nth-of-type(8) button {
        background-color: #49b156; color: white;
    }
    div[data-testid="stVerticalBlock"] > div:nth-of-type(9) button {
        background-color: #49b156; color: white;
    }

    /* Transpilation Node */
    div[data-testid="stVerticalBlock"] > div:nth-of-type(11) button {
        background-color: #FF8C00; color: black;
    }
                
    /* Target the main horizontal block that contains both columns */
    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }

    /* LEFT COLUMN (Flow canvas) */
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(1) {
        background-color: #1e1e1e;
    }

    /* RIGHT COLUMN (Node Palette) */
    div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) {
        background-color: #2b2b2b;
    }
    /* === DARK COLUMN BACKGROUNDS === */
div[data-testid="stHorizontalBlock"] > div:nth-of-type(1),
div[data-testid="stHorizontalBlock"] > div:nth-of-type(2) {
    background-color: #686868;  /* dark gray */
    border-radius: 12px;
}

/* === TEXT → WHITE === */
div[data-testid="stHorizontalBlock"] h1,
div[data-testid="stHorizontalBlock"] h2,
div[data-testid="stHorizontalBlock"] h3,
div[data-testid="stHorizontalBlock"] h4,
div[data-testid="stHorizontalBlock"] h5,
div[data-testid="stHorizontalBlock"] h6,
div[data-testid="stHorizontalBlock"] p,
div[data-testid="stHorizontalBlock"] label,
div[data-testid="stHorizontalBlock"] span {
    color: black !important;
}

/* === FIX BUTTON TEXT VISIBILITY === */
div[data-testid="stButton"] button {
    color: white;
}

/* === DIVIDER (looks better on dark) === */
hr {
    border-color: #555;
}


    </style>
    """, unsafe_allow_html=True)
    NODE_COLORS = {
        "input": "#4a86e8",
        "backend": "#744ae8",
        "compress": "#FFC878",
        "qucad": "#FFD700",
        "nocomp": "#FF6A50",
        "qbound": "#49b156",
        "simple": "#49b156",
        "transpile": "#4F30EA"
    }

    # Initialize Session State
    if 'flow_state' not in st.session_state:
        st.session_state.flow_state = StreamlitFlowState([], [])
    if 'backend_name' not in st.session_state:
        st.session_state.backend_name = "ibm_fez"

    st.set_page_config(layout="wide")

    col1, col2 = st.columns([4, 1.5])

    with col2:
        st.subheader("Node Palette")
        st.divider()

        # Helper function to prevent duplicates by checking ID
        def add_unique_node(node_id, content, color, node_type='default', label=None):
            # Filter out any existing node with this ID
            st.session_state.flow_state.nodes = [n for n in st.session_state.flow_state.nodes if n.id != node_id]
            
            new_node = StreamlitFlowNode(
                id=node_id, 
                pos=(50, 50),
                data={'content': content},
                node_type=node_type,
                label=label if label else content,
                draggable=True,
                style={"backgroundColor": color, "color": "black" if color in ["#FFC878", "#FFD700"] else "white"},
                selectable=True,
                deletable=True,
            )
            st.session_state.flow_state.nodes.append(new_node)

        with st.container(height=600, border=True):
            st.subheader("Input Nodes")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Circuit Node", key="btn_input"):
                    add_unique_node("input_node", "Circuit", NODE_COLORS["input"], "input")
            with c2:
                if st.button("Backend Node", key="btn_backend"):
                    add_unique_node("backend_node", "Backend", NODE_COLORS["backend"], "input")

            st.divider()
            st.subheader("Compression Nodes")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("CompressVQC", key="btn_compress"):
                    add_unique_node("compress_node", "CompressVQC", NODE_COLORS["compress"])
            with c2:
                if st.button("QuCAD", key="btn_qucad"):
                    add_unique_node("qucad_node", "QuCAD", NODE_COLORS["qucad"])
            
            if st.button("NoCompression", key="btn_nocomp"):
                add_unique_node("nocomp_node", "NoCompression", NODE_COLORS["nocomp"])

            st.divider()
            st.subheader("Fidelity Nodes")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("QuBound", key="btn_qbound"):
                    add_unique_node("qbound_node", "QuBound", NODE_COLORS["qbound"])
            with c2:
                if st.button("Simple Fid", key="btn_simple"):
                    add_unique_node("simple_node", "SimpleFid", NODE_COLORS["simple"])

            st.divider()
            st.subheader("Transpilation")
            if st.button("Transpile Node", key="btn_transpile"):
                add_unique_node("transpile_node", "Transpile", NODE_COLORS["transpile"])

    with col1:

        # Render Flow
        flow_state = streamlit_flow(
            'quantum_flow', 
            state=st.session_state.flow_state,
            height=500,
            fit_view=True,
            show_controls=True,          
            allow_new_edges=True,         
            animate_new_edges=True,      
            enable_node_menu=True,       
            enable_edge_menu=True, 
            get_node_on_click=True
        )

        if flow_state is not None:
            st.session_state.flow_state = flow_state

        # Node Property Editor
        if st.session_state.flow_state.selected_id:
            node_id = st.session_state.flow_state.selected_id
            st.divider()
            st.subheader(f"Settings: {node_id}")

            if "input_node" == node_id:
                st.file_uploader("Upload Circuit (.qpy)", type="qpy")
            
            elif "backend_node" == node_id:
                backend = st.selectbox("Select Target Backend:", ["ibm_fez", "ibm_marrakesh", "ibm_torino"])
                st.session_state.backend_name = backend

            elif "qucad_node" == node_id:
                st.info("QuCAD requires noise profile from Backend node.")
                st.radio("Optimization Mode", ["Start Fresh", "Use Previous QNN"], horizontal=True)

            elif "transpile_node" == node_id:
                st.slider("Qiskit Optimization Level", 0, 3, 1)

    # Action Buttons for the Flow
        act_c1, act_c2, act_c3 = st.columns([1,1,2])
        nodes_dict = {n.id: n for n in st.session_state.flow_state.nodes}
        st.write(nodes_dict)
        st.write(nodes_dict.get("input_node"))
        
        if act_c1.button("AUTOCONNECT", use_container_width=True):
            
            new_edges = []

            # Stage 1: Define Sequence Participants
            # Only one from each category can exist due to the unique ID system
            input_n = nodes_dict.get("input_node")
            backend_n = nodes_dict.get("backend_node")
            
            # Find which compression node is present
            comp_n = next((nodes_dict[i] for i in ["compress_node", "qucad_node", "nocomp_node"] if i in nodes_dict), None)
            
            # Find which fidelity node is present
            fid_n = next((nodes_dict[i] for i in ["qbound_node", "simple_node"] if i in nodes_dict), None)
            
            transpile_n = nodes_dict.get("transpile_node")

            # Stage 2: Build the Main Chain
            if input_n:
                current_source = input_n.id
                
                # Input -> Compression
                if comp_n:
                    new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{comp_n.id}", current_source, comp_n.id, animated=True))
                    current_source = comp_n.id
                
                # (Input or Compression) -> Fidelity
                if fid_n:
                    new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{fid_n.id}", current_source, fid_n.id, animated=True))
                    current_source = fid_n.id
                
                # (Input or Compression or Fidelity) -> Transpile
                if transpile_n:
                    new_edges.append(StreamlitFlowEdge(f"edge-{current_source}-{transpile_n.id}", current_source, transpile_n.id, animated=True))

            # Stage 3: Mandatory Backend Connections
            if backend_n:
                if "qucad_node" in nodes_dict:
                    new_edges.append(StreamlitFlowEdge("backend-to-qucad", backend_n.id, "qucad_node", animated=True, label="Noise Data"))
                if "qbound_node" in nodes_dict:
                    new_edges.append(StreamlitFlowEdge("backend-to-qbound", backend_n.id, "qbound_node", animated=True, label="Noise Data"))

            st.session_state.flow_state.edges = new_edges
            st.rerun()

        if act_c2.button("CLEAR CANVAS", use_container_width=True):
            st.session_state.flow_state = StreamlitFlowState([], [])
            st.rerun()

if __name__ == "__main__":
    flow_page()