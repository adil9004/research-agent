import streamlit as st
from research_agent import run_agent

st.set_page_config(page_title="AI Research Agent", page_icon="🔎", layout="centered")

st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="background: -webkit-linear-gradient(45deg, #7C5CFF, #4D8BFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">AI Research Agent</h1>
    <p style="color: #888;">Type any topic. Get a sourced research report in seconds.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([0.8, 0.2])
with col1:
    topic = st.text_input("", placeholder="e.g. top competitors of Notion in 2026", label_visibility="collapsed")
with col2:
    run_btn = st.button("Run", type="primary", use_container_width=True)

# Example topics section
ex_cols = st.columns(3)
example_topics = ["Best free AI tools 2026", "Electric scooter market India", "How RAG works"]
for i, ex in enumerate(example_topics):
    if ex_cols[i].button(ex, use_container_width=True):
        topic = ex
        run_btn = True

if run_btn and topic:
    final_answer = None
    error_msg = None
    with st.status("Researching...", expanded=True) as status:
        try:
            final_answer, steps = run_agent(topic, on_step=lambda s: status.write(s))
            if not final_answer or final_answer.startswith("No answer was produced"):
                status.update(label="Research failed", state="error")
            else:
                status.update(label="Research complete", state="complete")
        except Exception as e:
            error_msg = str(e)
            status.update(label="Research failed", state="error")

    if error_msg:
        st.error(f"An error occurred: {error_msg}")
    elif not final_answer or final_answer.startswith("No answer was produced"):
        st.warning("The agent returned no answer. Check the terminal.")
    elif final_answer is not None:
        # Split report and sources
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
        
        st.download_button(
            label="Download Report",
            data=final_answer,
            file_name="research_report.md",
            mime="text/markdown"
        )

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Built with Streamlit + Gemini</div>", unsafe_allow_html=True)
