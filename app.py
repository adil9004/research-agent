import streamlit as st
from research_agent import run_agent
import time
from urllib.parse import urlparse

st.set_page_config(page_title="AI Research Agent", page_icon="🔎", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');

    /* Global Styles */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    /* Main App Background */
    .stApp {
        background: radial-gradient(ellipse at 50% 0%, #10173a 0%, #070b1a 60%, #04060f 100%) !important;
        background-attachment: fixed !important;
    }

    /* Grid Layer */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: 0;
        pointer-events: none;
        background-image: 
            linear-gradient(rgba(0, 229, 255, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 229, 255, 0.06) 1px, transparent 1px);
        background-size: 48px 48px;
        mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
        -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
    }

    /* Glowing Orbs */
    .stApp::after {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: 0;
        pointer-events: none;
        background: 
            radial-gradient(circle at 20% 30%, rgba(0, 229, 255, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 80% 70%, rgba(124, 92, 255, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 50% 50%, rgba(255, 77, 216, 0.15) 0%, transparent 40%);
        animation: drift 25s ease-in-out infinite;
    }

    @keyframes drift {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(30px, -50px) scale(1.1); }
        66% { transform: translate(-30px, 30px) scale(0.9); }
    }

    /* Scanning Line */
    .stApp > div:first-child::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 1px;
        background: linear-gradient(90deg, transparent, #00E5FF, transparent);
        box-shadow: 0 0 8px #00E5FF;
        z-index: 10;
        pointer-events: none;
        animation: scan 8s linear infinite;
    }

    @keyframes scan {
        0% { top: 0; }
        100% { top: 100%; }
    }

    @media (prefers-reduced-motion: reduce) {
        .stApp::after, .stApp > div:first-child::before {
            animation: none !important;
        }
    }

    /* Content z-index */
    [data-testid="stVerticalBlock"] {
        position: relative;
        z-index: 1;
    }

    /* Futuristic Title */
    .futuristic-title {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700;
        letter-spacing: 2px;
        background: linear-gradient(45deg, #00E5FF, #7C5CFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
        font-size: 3rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    /* Glass cards */
    .stTextInput > div > div > input, 
    [data-testid="stRadio"], 
    .stButton > button:not([kind="primary"]),
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 16, 40, 0.55) !important;
        border: 1px solid rgba(0, 229, 255, 0.25) !important;
        border-radius: 14px !important;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:hover, 
    .stButton > button:not([kind="primary"]):hover,
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 0 16px rgba(0, 229, 255, 0.35);
        border-color: rgba(0, 229, 255, 0.5) !important;
        transform: translateY(-2px);
    }

    /* Run Button Styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(45deg, #00E5FF, #7C5CFF) !important;
        color: #070B1A !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 229, 255, 0.4);
        transition: all 0.3s ease;
    }

    .stButton > button[kind="primary"]:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(0, 229, 255, 0.6);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 class="futuristic-title">AI Research Agent</h1>
    <p style="color: #888;">Type any topic. Get a sourced research report in seconds.</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for recent searches
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []

# Input area
col1, col2 = st.columns([0.8, 0.2])
with col1:
    topic = st.text_input("", placeholder="e.g. top competitors of Notion in 2026", label_visibility="collapsed")
    depth = st.radio("Depth", ["Quick", "Deep"], horizontal=True)
with col2:
    run_btn = st.button("Run", type="primary", use_container_width=True)

# Example/Recent topics section
st.markdown("**Examples:**")
ex_cols = st.columns(3)
example_topics = ["Best free AI tools 2026", "Electric scooter market India", "How RAG works"]
for i, ex in enumerate(example_topics):
    if ex_cols[i].button(ex, use_container_width=True):
        topic = ex
        run_btn = True

if st.session_state.recent_searches:
    st.markdown("**Recent searches:**")
    rec_cols = st.columns(5)
    for i, r in enumerate(reversed(st.session_state.recent_searches)):
        if i < 5 and rec_cols[i].button(r, key=f"rec_{i}"):
            topic = r
            run_btn = True

if run_btn and topic:
    # Add to recent searches (unique and max 5)
    if topic not in st.session_state.recent_searches:
        st.session_state.recent_searches.append(topic)
        if len(st.session_state.recent_searches) > 5:
            st.session_state.recent_searches.pop(0)

    start_time = time.time()
    final_answer = None
    error_msg = None
    
    def format_step(step):
        if step.startswith("Searched:"):
            return f"🔍 **Searching:** {step.replace('Searched: ', '')}"
        elif step.startswith("Read:"):
            url = step.replace('Read: ', '')
            domain = urlparse(url).netloc
            return f"📄 **Reading:** {domain}"
        elif "report" in step.lower():
            return f"✍️ {step}"
        return step


    with st.status("Researching...", expanded=True) as status:
        try:
            final_answer, steps = run_agent(topic, depth=depth, on_step=lambda s: status.write(format_step(s)))
            status.write("✍️ **Writing the report...**")
            elapsed = time.time() - start_time
            status.write(f"✅ **Report ready in {elapsed:.1f} seconds**")
            status.update(label="Research complete", state="complete")
        except Exception as e:
            error_msg = str(e)
            status.update(label="Research failed", state="error")

    if error_msg:
        st.error(f"An error occurred: {error_msg}")
    elif not final_answer or final_answer.startswith("No answer was produced"):
        st.warning("The agent returned no answer. Check the terminal.")
    elif final_answer is not None:
        if "## Sources" in final_answer:
            parts = final_answer.split("## Sources")
            report_text = parts[0].strip()
            sources_text = parts[1].strip()
        else:
            report_text = final_answer
            sources_text = None

        with st.container(border=True):
            st.subheader("📄 Report")
            st.markdown(report_text)
            if sources_text:
                st.subheader("🔗 Sources")
                st.markdown(sources_text)
        
        st.download_button(label="Download Report", data=final_answer, file_name="research_report.md", mime="text/markdown")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Built with Streamlit + Gemini</div>", unsafe_allow_html=True)
