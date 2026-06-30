import streamlit as st
import asyncio
import nest_asyncio
from memory import add_notes, ask_question, reset_memory, generate_quiz, get_topics
from pypdf import PdfReader

nest_asyncio.apply()

st.set_page_config(page_title="StudyMate AI", page_icon="🧠", layout="centered")

# --- Sidebar: Topics ---
with st.sidebar:
    st.header("📚 Your Topics")
    if st.button("🔄 Refresh Topics", use_container_width=True):
        st.session_state.topics = asyncio.run(get_topics())

    if "topics" not in st.session_state:
        st.session_state.topics = asyncio.run(get_topics())

    if st.session_state.topics:
        for t in st.session_state.topics:
            last_studied = t["updated_at"]
            if last_studied:
                last_studied_str = str(last_studied).split(".")[0]
            else:
                last_studied_str = "Unknown"

            cols = st.columns([3, 1])
            with cols[0]:
                st.write(f"**{t['name']}**")
                st.caption(f"Last studied: {last_studied_str}")
            with cols[1]:
                if st.button("Use", key=f"switch_{t['name']}"):
                    st.session_state.dataset_name = t['name']
                    st.rerun()
    else:
        st.caption("No topics yet — add some notes to get started!")

st.title("🧠 StudyMate AI")
st.caption("Your memory-powered study assistant")

# --- Active topic selector (shared across all tabs) ---
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = "studymate"

st.session_state.dataset_name = st.text_input(
    "📌 Active topic:",
    value=st.session_state.dataset_name,
    help="All notes you add and questions you ask apply to this topic."
)
dataset_name = st.session_state.dataset_name

st.divider()

tab_notes, tab_ask, tab_quiz, tab_settings = st.tabs(
    ["📄 Add Notes", "💬 Ask", "📝 Quiz", "⚙️ Settings"]
)

# --- Tab 1: Add Notes (text + PDF) ---
with tab_notes:
    st.subheader("Paste Notes")
    notes_input = st.text_area("Paste your notes here:", height=200)

    if st.button("📥 Save to Memory", use_container_width=True):
        if notes_input.strip():
            with st.spinner("Building knowledge graph... (this may take a few mins ⏳)"):
                result = asyncio.run(add_notes(notes_input, dataset_name))
                st.success(result)
                st.session_state.topics = asyncio.run(get_topics())
        else:
            st.warning("Please paste some notes first!")

    st.divider()

    st.subheader("Upload PDF")
    pdf_file = st.file_uploader("Upload a PDF of your notes/textbook chapter:", type=["pdf"])

    if st.button("📥 Save PDF to Memory", use_container_width=True):
        if pdf_file is not None:
            with st.spinner("Extracting text from PDF..."):
                reader = PdfReader(pdf_file)
                pdf_text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pdf_text += extracted + "\n"

            if pdf_text.strip():
                with st.spinner("Building knowledge graph from PDF... (this may take a few mins ⏳)"):
                    result = asyncio.run(add_notes(pdf_text, dataset_name))
                    st.success(result)
                    st.session_state.topics = asyncio.run(get_topics())
            else:
                st.warning("Couldn't extract any text from this PDF. It might be a scanned/image-based PDF.")
        else:
            st.warning("Please upload a PDF first!")

# --- Tab 2: Ask a Question ---
with tab_ask:
    st.subheader("Ask a Question")
    question = st.text_input("What do you want to know?")

    if st.button("🔍 Ask", use_container_width=True):
        if question.strip():
            with st.spinner("Searching memory..."):
                results = asyncio.run(ask_question(question, dataset_name))
            st.subheader("Answer:")
            if results:
                for r in results:
                    if isinstance(r, dict) and "search_result" in r:
                        for answer in r["search_result"]:
                            st.write(answer)
                    else:
                        st.write(r)
            else:
                st.info("No results found. Try adding more notes first!")
        else:
            st.warning("Please type a question!")

# --- Tab 3: Quiz Me ---
with tab_quiz:
    st.subheader("Quiz Me")
    num_q = st.slider("Number of questions:", min_value=3, max_value=10, value=5)

    if st.button("🎯 Generate Quiz", use_container_width=True):
        with st.spinner("Generating quiz from your notes..."):
            quiz = asyncio.run(generate_quiz(dataset_name, num_q))
        if quiz:
            st.session_state.quiz = quiz
            st.session_state.quiz_submitted = False
        else:
            st.warning("Couldn't generate a quiz. Make sure you've added notes for this topic first!")

    if "quiz" in st.session_state and st.session_state.quiz:
        st.markdown(f"**Quiz: {dataset_name}**")
        user_answers = {}

        for i, q in enumerate(st.session_state.quiz):
            st.write(f"**Q{i+1}: {q['question']}**")
            user_answers[i] = st.radio(
                "Select an answer:",
                q["options"],
                key=f"q_{i}",
                label_visibility="collapsed"
            )

        if st.button("✅ Submit Quiz", use_container_width=True):
            score = 0
            for i, q in enumerate(st.session_state.quiz):
                selected_letter = user_answers[i][0]
                correct = q["correct_answer"]
                if selected_letter == correct:
                    score += 1
                    st.success(f"Q{i+1}: Correct! ✅")
                else:
                    st.error(f"Q{i+1}: Incorrect ❌ — Correct answer: {correct}")
            st.subheader(f"Final Score: {score}/{len(st.session_state.quiz)}")

# --- Tab 4: Settings ---
with tab_settings:
    st.subheader("Settings")
    st.write(f"Current active topic: **{dataset_name}**")
    st.divider()
    st.warning("This will permanently delete all stored notes and knowledge graphs.")
    if st.button("🗑️ Clear All Memory", use_container_width=True):
        with st.spinner("Clearing..."):
            result = asyncio.run(reset_memory())
        st.success(result)
        st.session_state.topics = []