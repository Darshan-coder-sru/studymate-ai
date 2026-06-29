import streamlit as st
import asyncio
import nest_asyncio
from memory import add_notes, ask_question, reset_memory

nest_asyncio.apply()

st.set_page_config(page_title="StudyMate AI", page_icon="🧠")

st.title("🧠 StudyMate AI")
st.caption("Your memory-powered study assistant")

# --- Section 1: Upload Notes ---
st.header("📄 Add Study Notes")
notes_input = st.text_area("Paste your notes here:", height=200)
dataset_name = st.text_input("Topic name (e.g. physics, history):", value="studymate")

if st.button("📥 Save to Memory"):
    if notes_input.strip():
       with st.spinner("Building knowledge graph... (this may take 2-5 mins on first run ⏳)"):
           result = asyncio.run(add_notes(notes_input, dataset_name))
           st.success(result)
    else:
        st.warning("Please paste some notes first!")

st.divider()

# --- Section 2: Ask a Question ---
st.header("💬 Ask a Question")
question = st.text_input("What do you want to know?")

if st.button("🔍 Ask"):
    if question.strip():
        with st.spinner("Searching memory..."):
            results = asyncio.run(ask_question(question))
        st.subheader("Answer:")
        if results:
            for r in results:
                st.write(r)
        else:
            st.info("No results found. Try adding more notes first!")
    else:
        st.warning("Please type a question!")

st.divider()

# --- Section 3: Reset ---
st.header("🗑️ Reset Memory")
if st.button("Clear All Memory"):
    with st.spinner("Clearing..."):
        result = asyncio.run(reset_memory())
    st.success(result)