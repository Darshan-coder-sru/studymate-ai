import streamlit as st
import asyncio
import re
import nest_asyncio
from memory import (
    add_notes, ask_question, reset_memory,
    generate_quiz, get_topics, save_struggle,
    get_weak_areas, generate_flashcards,
    generate_study_plan,
    delete_topic
)
from pypdf import PdfReader

nest_asyncio.apply()

st.set_page_config(page_title="StudyMate AI", page_icon="🧠", layout="centered")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
  --paper: #FBFBFE;
  --surface: #FFFFFF;
  --ink: #1E2233;
  --muted: #6B7280;
  --border: #E7E6F3;
  --violet: #6C63FF;
  --sky: #2EA8E0;
  --coral: #FF6B6B;
  --amber: #C9820A;
  --amber-bg: #F5A623;
  --teal: #12A594;
  --slate: #78829A;
  --shadow: 0 6px 20px rgba(30, 34, 51, 0.07);
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: var(--paper); }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; color: var(--ink); }

/* Hero header */
.sm-hero-title { font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:2.3rem; margin-bottom:.1rem;
  background: linear-gradient(90deg, var(--violet), var(--sky) 55%, var(--teal));
  -webkit-background-clip:text; background-clip:text; color:transparent; }
.sm-hero-tag { color: var(--muted); font-size:0.98rem; margin-top:-4px; margin-bottom:.9rem; }

/* Pills / badges */
.sm-pill { display:inline-flex; align-items:center; gap:.35rem; padding:.28rem .75rem; border-radius:999px;
  font-size:.8rem; font-weight:600; white-space:nowrap; }
.sm-pill-violet{ background:rgba(108,99,255,.12); color:var(--violet); }
.sm-pill-sky{ background:rgba(46,168,224,.14); color:#1c7ea6; }
.sm-pill-coral{ background:rgba(255,107,107,.14); color:#d84f4f; }
.sm-pill-amber{ background:rgba(245,166,35,.16); color:var(--amber); }
.sm-pill-teal{ background:rgba(18,165,148,.14); color:var(--teal); }
.sm-pill-slate{ background:rgba(120,130,154,.14); color:#4b5566; }

/* Sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #F4F2FF 0%, #FBFBFE 60%); border-right:1px solid var(--border); }

/* Card containers via st.container(border=True) */
[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); border-radius:16px !important;
  border:1px solid var(--border) !important; box-shadow: var(--shadow); }

/* Buttons */
.stButton > button, .stDownloadButton > button {
  border-radius:10px; font-weight:600; border:1.5px solid var(--border);
  background: var(--surface) !important; color: var(--ink) !important;
  transition: transform .12s ease, box-shadow .12s ease; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
.stButton > button p { color: var(--ink) !important; }
button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background: linear-gradient(90deg, var(--accent, var(--violet)), var(--sky)) !important;
  border:none !important; color:#fff !important; }
button[kind="primary"] p, [data-testid="stBaseButton-primary"] p { color:#fff !important; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div {
  border-radius:10px !important; border:1.5px solid var(--border) !important;
  background: var(--surface) !important; color: var(--ink) !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--violet) !important; box-shadow: 0 0 0 3px rgba(108,99,255,.15) !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--muted) !important; }

/* Body / label / caption text stays legible regardless of system theme */
.stMarkdown, .stMarkdown p, label, .stCaptionContainer, [data-testid="stWidgetLabel"] p {
  color: var(--ink) !important; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface) !important; border-radius:10px !important; }
[data-testid="stFileUploaderDropzone"] * { color: var(--ink) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; padding:8px 16px; font-weight:600; color:var(--muted); }
.stTabs [data-baseweb="tab-list"] button:nth-child(1) { --accent: var(--violet); }
.stTabs [data-baseweb="tab-list"] button:nth-child(2) { --accent: var(--sky); }
.stTabs [data-baseweb="tab-list"] button:nth-child(3) { --accent: var(--coral); }
.stTabs [data-baseweb="tab-list"] button:nth-child(4) { --accent: var(--amber-bg); }
.stTabs [data-baseweb="tab-list"] button:nth-child(5) { --accent: var(--teal); }
.stTabs [data-baseweb="tab-list"] button:nth-child(6) { --accent: var(--slate); }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--accent) !important;
  border-bottom:3px solid var(--accent) !important; }

/* Scope an accent color to each tab panel's content */
.stTabs [data-baseweb="tab-panel"]:nth-of-type(1) { --accent: var(--violet); }
.stTabs [data-baseweb="tab-panel"]:nth-of-type(2) { --accent: var(--sky); }
.stTabs [data-baseweb="tab-panel"]:nth-of-type(3) { --accent: var(--coral); }
.stTabs [data-baseweb="tab-panel"]:nth-of-type(4) { --accent: var(--amber-bg); }
.stTabs [data-baseweb="tab-panel"]:nth-of-type(5) { --accent: var(--teal); }
.stTabs [data-baseweb="tab-panel"]:nth-of-type(6) { --accent: var(--slate); }
.stTabs [data-baseweb="tab-panel"] [data-testid="stVerticalBlockBorderWrapper"] { border-top:4px solid var(--accent) !important; }
.stTabs [data-baseweb="tab-panel"] h3 { color: var(--accent) !important; }

/* Alerts */
.stAlert { border-radius:12px !important; }

/* Metrics */
[data-testid="stMetric"] { background: var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:.5rem .7rem; }
[data-testid="stMetricValue"] { font-family:'IBM Plex Mono', monospace !important; color: var(--violet); }

/* Expander */
[data-testid="stExpander"] { border-radius:14px !important; border:1px solid var(--border) !important; overflow:hidden; }

/* Flashcards */
.sm-flashcard { background: var(--surface); border:2px solid var(--amber-bg); border-radius:20px;
  padding:2.4rem 1.6rem; text-align:center; font-size:1.25rem; font-weight:600; color:var(--ink);
  box-shadow: var(--shadow); min-height:130px; display:flex; align-items:center; justify-content:center; }
.sm-flashcard.back { border-color: var(--teal); background: rgba(18,165,148,.06); }

/* Weak-area cards */
.sm-weak-card { border-left:4px solid var(--coral); background:rgba(255,107,107,.06); border-radius:10px;
  padding:.5rem .8rem; margin-bottom:.45rem; font-size:.88rem; color:var(--ink); }

/* Score card */
.sm-score-card { border-radius:16px; padding:1.1rem 1.4rem; text-align:center; font-family:'Space Grotesk',sans-serif;
  font-weight:700; font-size:1.5rem; box-shadow: var(--shadow); margin:.6rem 0 1rem 0; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def sanitize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())


def check_achievements(session: dict) -> list:
    earned = []
    scores = session.get("quiz_scores", [])
    topics = session.get("topics", [])

    if len(scores) >= 1:
        earned.append(("🎯", "First Quiz!", "You completed your first quiz"))
    if any(s["pct"] == 100 for s in scores):
        earned.append(("🏆", "Perfect Score!", "You scored 100% on a quiz"))
    if len(scores) >= 5:
        earned.append(("🔥", "Quiz Streak!", "You completed 5 quizzes"))
    if len(topics) >= 3:
        earned.append(("📚", "Knowledge Seeker!", "You added 3+ topics"))
    if len(topics) >= 5:
        earned.append(("🧠", "Brain Power!", "You added 5+ topics"))
    if session.get("flashcards"):
        earned.append(("🔁", "Flashcard Fan!", "You generated flashcards"))
    if session.get("study_plan"):
        earned.append(("📅", "Planner Pro!", "You generated a study plan"))
    if scores and sum(s["pct"] for s in scores) / len(scores) >= 80:
        earned.append(("⭐", "High Achiever!", "Your average quiz score is 80%+"))

    return earned


# --- Sidebar ---
with st.sidebar:
    st.header("📚 Your Topics")
    if st.button("🔄 Refresh Topics", use_container_width=True):
        st.session_state.topics = asyncio.run(get_topics())

    if "topics" not in st.session_state:
        st.session_state.topics = asyncio.run(get_topics())

    if st.session_state.topics:
        for t in st.session_state.topics:
            last_studied = t["updated_at"]
            last_studied_str = str(last_studied).split(".")[0] if last_studied else "Unknown"
            with st.container(border=True):
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(
                        f'<span class="sm-pill sm-pill-violet">📌 {t["name"]}</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Last studied: {last_studied_str}")
                with cols[1]:
                    if st.button("Use", key=f"switch_{t['name']}"):
                        st.session_state.dataset_name = t["name"]
                        st.rerun()
                with cols[2]:
                    if st.button("🗑️", key=f"delete_{t['name']}", help=f"Delete topic {t['name']}"):
                        with st.spinner(f"Deleting {t['name']}..."):
                            result = asyncio.run(delete_topic(t["name"]))
                        st.toast(result)
                        st.session_state.topics = asyncio.run(get_topics())
                        st.rerun()
    else:
        st.caption("No topics yet — add some notes to get started!")

    st.divider()

    # --- Study Progress ---
    st.subheader("📊 Study Progress")
    if "quiz_scores" not in st.session_state:
        st.session_state.quiz_scores = []

    if st.session_state.quiz_scores:
        total_quizzes = len(st.session_state.quiz_scores)
        avg_score = sum(s["pct"] for s in st.session_state.quiz_scores) / total_quizzes
        best_score = max(s["pct"] for s in st.session_state.quiz_scores)
        with st.container(border=True):
            st.metric("Quizzes Taken", total_quizzes)
            st.metric("Average Score", f"{avg_score:.0f}%")
            st.metric("Best Score", f"{best_score:.0f}%")
        st.caption("Recent quizzes:")
        for s in st.session_state.quiz_scores[-3:][::-1]:
            st.caption(f"• {s['topic']}: {s['score']}/{s['total']} ({s['pct']:.0f}%)")
    else:
        st.caption("No quizzes taken yet!")

    st.divider()

    # --- Weak Areas ---
    st.subheader("⚠️ Weak Areas")
    if "weak_areas" not in st.session_state:
        st.session_state.weak_areas = asyncio.run(get_weak_areas())
    if st.button("🔄 Refresh Weak Areas", use_container_width=True):
        st.session_state.weak_areas = asyncio.run(get_weak_areas())
    if st.session_state.weak_areas:
        weak_html = "".join(f'<div class="sm-weak-card">⚠️ {w}</div>' for w in st.session_state.weak_areas)
        st.markdown(weak_html, unsafe_allow_html=True)
    else:
        st.caption("No weak areas yet — take a quiz first!")

    st.divider()

    # --- Achievements ---
    st.subheader("🏅 Achievements")
    achievements = check_achievements(st.session_state)
    if achievements:
        pill_styles = ["sm-pill-violet", "sm-pill-sky", "sm-pill-coral", "sm-pill-amber", "sm-pill-teal"]
        for i, (icon, title, desc) in enumerate(achievements):
            style = pill_styles[i % len(pill_styles)]
            st.markdown(
                f'<span class="sm-pill {style}">{icon} {title}</span>',
                unsafe_allow_html=True,
            )
            st.caption(desc)
    else:
        st.caption("No achievements yet — keep studying!")


# --- Main ---
st.markdown('<div class="sm-hero-title">🧠 StudyMate AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-hero-tag">Your memory-powered study assistant</div>', unsafe_allow_html=True)

if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = "studymate"

st.session_state.dataset_name = st.text_input(
    "📌 Active topic:",
    value=st.session_state.dataset_name,
    help="All notes you add and questions you ask apply to this topic."
)
dataset_name = st.session_state.dataset_name
clean_name = sanitize_name(dataset_name)

st.markdown(f'<span class="sm-pill sm-pill-violet">📖 Studying: {clean_name}</span>', unsafe_allow_html=True)

if clean_name != dataset_name:
    st.caption(f"⚠️ Topic will be saved as: `{clean_name}` (spaces/dots not allowed)")

st.divider()

tab_notes, tab_ask, tab_quiz, tab_flash, tab_plan, tab_settings = st.tabs(
    ["📄 Notes", "💬 Ask", "📝 Quiz", "🔁 Flashcards", "📅 Study Plan", "⚙️ Settings"]
)

# --- Tab 1: Add Notes ---
with tab_notes:
    with st.container(border=True):
        st.subheader("Paste Notes")
        notes_input = st.text_area("Paste your notes here:", height=200)

        if st.button("📥 Save to Memory", use_container_width=True, type="primary"):
            if notes_input.strip():
                with st.spinner("Building knowledge graph... (this may take a few mins ⏳)"):
                    result = asyncio.run(add_notes(notes_input, dataset_name))
                    st.success(result)
                    st.session_state.topics = asyncio.run(get_topics())
            else:
                st.warning("Please paste some notes first!")

    st.write("")

    with st.container(border=True):
        st.subheader("Upload PDF")
        pdf_file = st.file_uploader("Upload a PDF of your notes/textbook chapter:", type=["pdf"])

        if st.button("📥 Save PDF to Memory", use_container_width=True, type="primary"):
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
                    st.warning("Couldn't extract text. It might be a scanned/image-based PDF.")
            else:
                st.warning("Please upload a PDF first!")

# --- Tab 2: Ask ---
with tab_ask:
    with st.container(border=True):
        st.subheader("Ask a Question")
        question = st.text_input("What do you want to know?")

        difficulty = st.select_slider(
            "🎯 Difficulty level:",
            options=["Beginner", "Intermediate", "Advanced"],
            value="Intermediate"
        )

        if st.button("🔍 Ask", use_container_width=True, type="primary"):
            if question.strip():
                with st.spinner("Searching memory and generating adaptive answer..."):
                    results = asyncio.run(ask_question(question, dataset_name, difficulty))
                st.markdown("---")
                st.markdown(f'<span class="sm-pill sm-pill-sky">📌 Difficulty: {difficulty}</span>', unsafe_allow_html=True)
                st.caption("Based on your notes and struggle history")
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

# --- Tab 3: Quiz ---
with tab_quiz:
    with st.container(border=True):
        st.subheader("Quiz Me")
        num_q = st.slider("Number of questions:", min_value=3, max_value=10, value=5)

        if st.button("🎯 Generate Quiz", use_container_width=True, type="primary"):
            with st.spinner("Generating quiz from your notes..."):
                quiz = asyncio.run(generate_quiz(dataset_name, num_q))
            if quiz:
                st.session_state.quiz = quiz
                st.session_state.quiz_submitted = False
            else:
                st.warning("Couldn't generate a quiz. Make sure you have added notes first!")

    if "quiz" in st.session_state and st.session_state.quiz:
        st.write("")
        with st.container(border=True):
            st.markdown(f'<span class="sm-pill sm-pill-coral">📝 Quiz: {clean_name}</span>', unsafe_allow_html=True)
            st.write("")
            user_answers = {}

            for i, q in enumerate(st.session_state.quiz):
                st.write(f"**Q{i+1}: {q['question']}**")
                user_answers[i] = st.radio(
                    "Select an answer:",
                    q["options"],
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )

            if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                score = 0
                for i, q in enumerate(st.session_state.quiz):
                    selected_letter = user_answers[i][0]
                    correct = q["correct_answer"]
                    if selected_letter == correct:
                        score += 1
                        st.success(f"Q{i+1}: Correct! ✅")
                    else:
                        st.error(f"Q{i+1}: Incorrect ❌ — Correct answer: {correct}")
                        asyncio.run(save_struggle(
                            dataset_name,
                            q["question"],
                            correct,
                            selected_letter
                        ))

                total = len(st.session_state.quiz)
                pct = (score / total) * 100
                if pct >= 80:
                    score_color, score_bg = "#0F9D58", "rgba(15,157,88,.1)"
                elif pct >= 50:
                    score_color, score_bg = "#C9820A", "rgba(245,166,35,.14)"
                else:
                    score_color, score_bg = "#d84f4f", "rgba(255,107,107,.12)"
                st.markdown(
                    f'<div class="sm-score-card" style="color:{score_color}; background:{score_bg};">'
                    f'Final Score: {score}/{total} ({pct:.0f}%)</div>',
                    unsafe_allow_html=True,
                )

                st.session_state.quiz_scores.append({
                    "topic": clean_name,
                    "score": score,
                    "total": total,
                    "pct": pct
                })
                st.session_state.weak_areas = asyncio.run(get_weak_areas())

# --- Tab 4: Flashcards ---
with tab_flash:
    with st.container(border=True):
        st.subheader("🔁 Flashcards")
        num_cards = st.slider("Number of flashcards:", min_value=3, max_value=15, value=5)

        if st.button("✨ Generate Flashcards", use_container_width=True, type="primary"):
            with st.spinner("Generating flashcards from your notes..."):
                cards = asyncio.run(generate_flashcards(dataset_name, num_cards))
            if cards:
                st.session_state.flashcards = cards
                st.session_state.card_index = 0
                st.session_state.card_flipped = False
            else:
                st.warning("Couldn't generate flashcards. Add some notes first!")

    if "flashcards" in st.session_state and st.session_state.flashcards:
        cards = st.session_state.flashcards
        idx = st.session_state.card_index
        flipped = st.session_state.card_flipped
        total_cards = len(cards)

        st.write("")
        st.markdown(
            f'<span class="sm-pill sm-pill-amber">🔁 Card {idx + 1} of {total_cards}</span>',
            unsafe_allow_html=True,
        )
        st.write("")
        card = cards[idx]

        if not flipped:
            st.markdown(f'<div class="sm-flashcard">{card["front"]}</div>', unsafe_allow_html=True)
            st.write("")
            if st.button("👁️ Reveal Answer", use_container_width=True, type="primary"):
                st.session_state.card_flipped = True
                st.rerun()
        else:
            st.markdown(f'<div class="sm-flashcard back">{card["back"]}</div>', unsafe_allow_html=True)
            st.write("")
            if st.button("🔁 Flip Back", use_container_width=True, type="primary"):
                st.session_state.card_flipped = False
                st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.card_index = max(0, idx - 1)
                st.session_state.card_flipped = False
                st.rerun()
        with col2:
            if st.button("➡️ Next", use_container_width=True):
                st.session_state.card_index = min(total_cards - 1, idx + 1)
                st.session_state.card_flipped = False
                st.rerun()

# --- Tab 5: Study Plan ---
with tab_plan:
    with st.container(border=True):
        st.subheader("📅 AI Study Plan")
        days = st.slider("Plan duration (days):", min_value=3, max_value=14, value=7)

        if st.button("🧠 Generate Study Plan", use_container_width=True, type="primary"):
            with st.spinner("Generating your personalized study plan..."):
                plan = asyncio.run(generate_study_plan(dataset_name, days))
            if plan:
                st.session_state.study_plan = plan
            else:
                st.warning("Couldn't generate a study plan. Add some notes first!")

    if "study_plan" in st.session_state and st.session_state.study_plan:
        st.write("")
        for day in st.session_state.study_plan:
            with st.expander(f"📅 Day {day['day']} — {day['focus']}"):
                for task in day["tasks"]:
                    st.write(f"• {task}")
                st.info(f"💡 Tip: {day['tip']}")

# --- Tab 6: Settings ---
with tab_settings:
    with st.container(border=True):
        st.subheader("Settings")
        st.markdown(f'<span class="sm-pill sm-pill-slate">📖 Current active topic: {clean_name}</span>', unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.subheader("🗑️ Delete a Topic")
        if st.session_state.topics:
            topic_to_delete = st.selectbox(
                "Select topic to delete:",
                [t["name"] for t in st.session_state.topics]
            )
            if st.button("🗑️ Delete Selected Topic", use_container_width=True):
                with st.spinner(f"Deleting {topic_to_delete}..."):
                    result = asyncio.run(delete_topic(topic_to_delete))
                st.success(result)
                st.session_state.topics = asyncio.run(get_topics())
                st.rerun()
        else:
            st.caption("No topics to delete yet!")

    st.write("")

    with st.container(border=True):
        st.warning("This will permanently delete all stored notes and knowledge graphs.")
        if st.button("🗑️ Clear All Memory", use_container_width=True):
            with st.spinner("Clearing..."):
                result = asyncio.run(reset_memory())
            st.success(result)
            st.session_state.topics = []
            st.session_state.weak_areas = []
            st.session_state.quiz_scores = []
            st.session_state.study_plan = []