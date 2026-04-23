import streamlit as st
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