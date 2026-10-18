import streamlit as st
from research_agent import run_agent

st.title("Research Agent")
topic = st.text_input("Enter a topic:")
if st.button("Run"):
    if topic:
        final_answer = None
        error_msg = None
        with st.status("Researching...", expanded=True) as status:
            try:
                # Pass a callback that writes each step to the status container
                final_answer, steps = run_agent(topic, on_step=lambda s: status.write(s))
                # Steps have already been written to the status container via the callback
                # Check if final_answer indicates failure (None or "No answer was produced")
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
            st.write("### Report")
            st.write(final_answer)
            st.download_button(
                label="Download Report",
                data=final_answer,
                file_name="research_report.md",
                mime="text/markdown"
            )
