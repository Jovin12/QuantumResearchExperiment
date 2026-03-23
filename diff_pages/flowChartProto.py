import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode
from streamlit_flow.state import StreamlitFlowState

def flow_page():
    # Injecting CSS
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
    background-color: #484848;  /* dark gray */
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



    # Session state (UNCHANGED)
    if 'flow_state' not in st.session_state:
        st.session_state.flow_state = StreamlitFlowState([], [])
    if 'input_node_id' not in st.session_state:
        st.session_state.input_node_id = 0
    if 'node_id' not in st.session_state:
        st.session_state.node_id = 0
    if 'backend_name' not in st.session_state:
        st.session_state.backend_name = "IbmFez"
    if 'compress_node_id' not in st.session_state: 
        st.session_state.compress_node_id = 0
    if 'qucad_node_id' not in st.session_state: 
        st.session_state.qucad_node_id = 0
    if 'no_comp_node_id' not in st.session_state: 
        st.session_state.no_comp_node_id = 0
    if 'qbound_node_id' not in st.session_state: 
        st.session_state.qbound_node_id = 0
    if 'simple_node_id' not in st.session_state:
        st.session_state.simple_node_id = 0
    if 'transpile_node' not in st.session_state:
        st.session_state.transpile_node = 'Transpile'
    if 'selected_node' not in st.session_state: 
        st.session_state.selected_node = None

    st.set_page_config(layout="wide")

    col1, col2 = st.columns([4, 1.5])

    with col2:
        st.subheader("Node Palette")
        st.divider()

        with st.container(height=600, border=True):

            st.subheader("Input Nodes")
            c1, c2 = st.columns(2)

            with c1:
                if st.button("Circuit Node", key="btn_input"):
                    st.session_state.input_node_id += 1
                    id = "input_" + str(st.session_state.input_node_id)
                    new_id = str(st.session_state.input_node_id)
                    new_node = StreamlitFlowNode(
                        id=id, pos=(50, 50),
                        data={
                            'content': f'Circuit_{new_id}',
                            'color': NODE_COLORS["input"]
                        },
                        node_type='input',
                        label=f'Input {new_id}',
                        draggable=True,
                        style={"backgroundColor": NODE_COLORS["input"]},
                        selectable=True,
                        deletable=True,
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            with c2:
                if st.button("Circuit Backend Node", key="btn_backend"):
                    new_name = str(st.session_state.backend_name)
                    new_node = StreamlitFlowNode(
                        id=new_name, pos=(50, 50),
                        data={'content': f'Backend'},
                        node_type='input',
                        label=f'Input {new_name}',
                        draggable=True,
                        style = {'backgroundColor': NODE_COLORS['backend']},
                        selectable=True,
                        deletable=True,
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            st.divider()

            st.subheader("Compression Nodes")
            c1, c2 = st.columns(2)

            with c1:
                if st.button(" CompressVQC Node", key="btn_compress"):
                    st.session_state.compress_node_id += 1
                    id = "compress_" + str(st.session_state.compress_node_id)
                    new_id = str(st.session_state.compress_node_id)
                    new_node = StreamlitFlowNode(
                        id=id, pos=(50, 50),
                        data={
                            'content': f'CompressVQC{new_id}',
                            'color': NODE_COLORS["compress"]
                        },
                        node_type='default',
                        label=f'Process {new_id}',
                        draggable=True,
                        style={"backgroundColor": NODE_COLORS["compress"]},
                        selectable=True,
                        deletable=True,
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            with c2:
                if st.button("QuCAD Node", key="btn_qucad"):
                    st.session_state.qucad_node_id += 1
                    id = "qucad_" + str(st.session_state.qucad_node_id)
                    new_id = str(st.session_state.qucad_node_id)
                    new_node = StreamlitFlowNode(
                        id=id, pos=(50, 50),
                        data={'content': f'QuCAD_{new_id}'},
                        node_type='default',
                        label=f'Process {new_id}',
                        draggable=True,
                        selectable=True,
                        deletable=True,
                        style={"backgroundColor": NODE_COLORS["qucad"]}
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                if st.button("NoCompression Node", key="btn_nocomp"):
                    st.session_state.no_comp_node_id += 1
                    id = 'nocomp_' + str(st.session_state.no_comp_node_id)
                    new_id = str(st.session_state.no_comp_node_id)
                    new_node = StreamlitFlowNode(
                        id=id, pos=(50, 50),
                        data={'content': f'NoCompression_{new_id}'},
                        node_type='default',
                        label=f'Process {new_id}',
                        draggable=True,
                        selectable=True,
                        deletable=True,
                        style={"backgroundColor": NODE_COLORS["nocomp"]}
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            st.divider()

            st.subheader("Fidelity Nodes")
            c1, c2 = st.columns(2)

            with c1:
                if st.button("QuBound Node", key="btn_qbound"):
                    st.session_state.qbound_node_id += 1
                    id = 'qbound_' + str(st.session_state.qbound_node_id)
                    new_id = str(st.session_state.qbound_node_id)
                    new_node = StreamlitFlowNode(
                        id=id, pos=(50, 50),
                        data={'content': f'QuBound_{new_id}'},
                        node_type='default',
                        label=f'Process {new_id}',
                        draggable=True,
                        style={"backgroundColor": NODE_COLORS["qbound"]},
                        selectable=True,
                        deletable=True,
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            with c2:
                if st.button("Simple/Simulated Fidelity Node", key="btn_simple"):
                    st.session_state.simple_node_id += 1
                    id = 'simple_' + str(st.session_state.simple_node_id)
                    new_id = str(st.session_state.simple_node_id)
                    new_node = StreamlitFlowNode(
                        id=id, pos=(50, 50),
                        data={'content': f'SimpleFid_{new_id}'},
                        node_type='default',
                        label=f'Process {new_id}',
                        draggable=True,
                        selectable=True,
                        deletable=True,
                        style={"backgroundColor": NODE_COLORS["simple"]}
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

            st.divider()

            st.subheader("Transpilation Nodes")

            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                if st.button("Transpilation Node", key="btn_transpile"):
                    unique_transpile_id = "transpile_unique"
                    new_node = StreamlitFlowNode(
                        id=unique_transpile_id, pos=(50, 50),
                        data={'content': f'Transpile'},
                        node_type='default',
                        label=f'Process {unique_transpile_id}',
                        draggable=True,
                        selectable=True,
                        deletable=True,
                        style={"backgroundColor": NODE_COLORS["transpile"]}
                    )
                    st.session_state.flow_state.nodes.append(new_node)
                    # st.rerun()

                st.divider()

    with col1:
        flow_state = streamlit_flow(
            'my_flow', 
            state=st.session_state.flow_state,
            height=500,
            fit_view=True,
            show_controls=True,          
            allow_new_edges=True,         
            animate_new_edges=True,      
            enable_node_menu=True,       
            enable_edge_menu=True, 
            get_node_on_click=True,
            get_edge_on_click=True      
        )

        if flow_state is not None:
            st.session_state.flow_state = flow_state

            # st.write(st.session_state.flow_state)
            # st.write(st.session_state.flow_state.selected_id)

            with st.container():
                if st.session_state.flow_state.selected_id is not None:

                    st.session_state.selected_node = st.session_state.flow_state.selected_id
                    node_name = st.session_state.selected_node
                    st.header(node_name)

                    if "input" in str(node_name):
                        st.file_uploader(label="Upload your circuit qpy file Here:", type="qpy")
                    
                    if "IbmFez" in str(node_name):
                        backend = st.selectbox("Select Backends:", options=["ibm_fez", "ibm_marrakesh", "ibm_torino"])
                        st.session_state.backend_name = backend

                    if "qucad" in str(node_name):
                        QuCAD_option = st.radio(
                            label="noise_opt",
                            options=["User Previous QNN optimization","Start Fresh"],
                            index=1,
                            horizontal=True,
                            label_visibility="collapsed",
                        )

                        if QuCAD_option == "Start Fresh":
                            st.warning("You have selected QUCAD which require the day of the noise you want to simulate.")
                            
                        elif QuCAD_option == "User Previous QNN optimization":
                            # st.write("huh")
                            model_name = st.text_input("Enter your unique name for this QuCAD model you want to use :")

                    if 'qbound' in str(node_name):
                        Qubound_option = st.radio(
                            label= 'fid_option',
                            options = ["Use Pretrained QuBound Model", "Start Fresh QuBound"],
                            index = 1, 
                            horizontal = True, 
                            label_visibility = 'collapsed'
                        )
                        if Qubound_option == "Start Fresh QuBound":
                            st.warning("You have selected QUCAD which require the day of the noise you want to simulate.")
                        elif Qubound_option == 'Use Pretrained QuBound Model':
                            model_name = st.text_input("Enter your unique name for this QuCAD model you want to use :")
                    
                    if 'transpile' in str(node_name):
                        optim_map = {
                            "0: NO QISKIT OPTMIZATION": 0,
                            "1: LIGHT OPTMIZATION; Basic gate folding": 1,
                            "2: MEDIUM; Commutative analysis": 2,
                            "3: HEAVY; Deep pulse-levl Optimization": 3
                        }
                        optmization_choice = st.selectbox("Select qiskit Optimization Level:", options=list(optim_map.keys()), label_visibility="hidden")
                    
                    if 'simple' in str(node_name):
                        pass
                    if 'compress' in str(node_name):
                        pass
                    if 'nocomp' in str(node_name):
                        pass
