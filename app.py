import streamlit as st
import asyncio
import re
import nest_asyncio
import memory
from memory import (
    add_notes, ask_question, reset_memory,
    generate_quiz, get_topics, save_struggles_batch,
    get_weak_areas, generate_flashcards,
    generate_study_plan,
    delete_topic,
    get_knowledge_graph,
    get_learning_dna,
    predict_exam,
)
from pypdf import PdfReader
import streamlit.components.v1 as components

nest_asyncio.apply()

st.set_page_config(page_title="StudyMate AI", page_icon="🧠", layout="centered")


def get_event_loop():
    if "event_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        st.session_state.event_loop = loop
    return st.session_state.event_loop


def run_async(coro):
    loop = get_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def run_async_safe(coro, friendly_message="Something went wrong. Please try again."):
    try:
        return run_async(coro)
    except Exception as e:
        st.error(f"⚠️ {friendly_message}")
        with st.expander("Technical details"):
            st.code(f"{type(e).__name__}: {e}")
        return None
        # Apply backend mode from session state on every page load
_backend_mode = st.session_state.get("backend_choice", "Local (Ollama)")
memory.set_mode("cloud" if _backend_mode == "Cloud (Cognee)" else "local")

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

.sm-hero-title { font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:2.3rem; margin-bottom:.1rem;
  background: linear-gradient(90deg, var(--violet), var(--sky) 55%, var(--teal));
  -webkit-background-clip:text; background-clip:text; color:transparent; }
.sm-hero-tag { color: var(--muted); font-size:0.98rem; margin-top:-4px; margin-bottom:.9rem; }

.sm-pill { display:inline-flex; align-items:center; gap:.35rem; padding:.28rem .75rem; border-radius:999px;
  font-size:.8rem; font-weight:600; white-space:nowrap; }
.sm-pill-violet{ background:rgba(108,99,255,.12); color:var(--violet); }
.sm-pill-sky{ background:rgba(46,168,224,.14); color:#1c7ea6; }
.sm-pill-coral{ background:rgba(255,107,107,.14); color:#d84f4f; }
.sm-pill-amber{ background:rgba(245,166,35,.16); color:var(--amber); }
.sm-pill-teal{ background:rgba(18,165,148,.14); color:var(--teal); }
.sm-pill-slate{ background:rgba(120,130,154,.14); color:#4b5566; }

[data-testid="stSidebar"] { background: linear-gradient(180deg, #F4F2FF 0%, #FBFBFE 60%); border-right:1px solid var(--border); }

[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); border-radius:16px !important;
  border:1px solid var(--border) !important; box-shadow: var(--shadow); }

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

.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div {
  border-radius:10px !important; border:1.5px solid var(--border) !important;
  background: var(--surface) !important; color: var(--ink) !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--violet) !important; box-shadow: 0 0 0 3px rgba(108,99,255,.15) !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--muted) !important; }

.stMarkdown, .stMarkdown p, label, .stCaptionContainer, [data-testid="stWidgetLabel"] p {
  color: var(--ink) !important; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface) !important; border-radius:10px !important; }
[data-testid="stFileUploaderDropzone"] * { color: var(--ink) !important; }

.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius:10px 10px 0 0; padding:8px 16px; font-weight:600; color:var(--muted); }
.stTabs [data-baseweb="tab-list"] button:nth-child(1) { --accent: var(--violet); }
.stTabs [data-baseweb="tab-list"] button:nth-child(2) { --accent: var(--sky); }
.stTabs [data-baseweb="tab-list"] button:nth-child(3) { --accent: var(--coral); }
.stTabs [data-baseweb="tab-list"] button:nth-child(4) { --accent: var(--amber-bg); }
.stTabs [data-baseweb="tab-list"] button:nth-child(5) { --accent: var(--teal); }
.stTabs [data-baseweb="tab-list"] button:nth-child(6) { --accent: var(--slate); }
.stTabs [data-baseweb="tab-list"] button:nth-child(7) { --accent: var(--violet); }
.stTabs [data-baseweb="tab-list"] button:nth-child(8) { --accent: var(--sky); }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--accent) !important;
  border-bottom:3px solid var(--accent) !important; }

.stAlert { border-radius:12px !important; }

[data-testid="stMetric"] { background: var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:.5rem .7rem; }
[data-testid="stMetricValue"] { font-family:'IBM Plex Mono', monospace !important; color: var(--violet); }

[data-testid="stExpander"] { border-radius:14px !important; border:1px solid var(--border) !important; overflow:hidden; }

.sm-flashcard { background: var(--surface); border:2px solid var(--amber-bg); border-radius:20px;
  padding:2.4rem 1.6rem; text-align:center; font-size:1.25rem; font-weight:600; color:var(--ink);
  box-shadow: var(--shadow); min-height:130px; display:flex; align-items:center; justify-content:center; }
.sm-flashcard.back { border-color: var(--teal); background: rgba(18,165,148,.06); }

.sm-weak-card { border-left:4px solid var(--coral); background:rgba(255,107,107,.06); border-radius:10px;
  padding:.5rem .8rem; margin-bottom:.45rem; font-size:.88rem; color:var(--ink); }

.sm-score-card { border-radius:16px; padding:1.1rem 1.4rem; text-align:center; font-family:'Space Grotesk',sans-serif;
  font-weight:700; font-size:1.5rem; box-shadow: var(--shadow); margin:.6rem 0 1rem 0; }

/* ── DNA Dashboard ── */
.dna-card {
  background: linear-gradient(135deg, #F4F2FF 0%, #EAF8F5 100%);
  border: 1px solid var(--border); border-radius: 18px;
  padding: 1.4rem 1.6rem; margin-bottom: 1rem;
}
.dna-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.1rem; font-weight: 700; color: var(--violet);
  margin-bottom: .8rem; letter-spacing: -0.01em;
}
.dna-bar-wrap { margin: .35rem 0 .65rem; }
.dna-bar-label { font-size: .82rem; font-weight: 600; color: var(--ink); margin-bottom: .2rem; }
.dna-bar-bg { background: #E7E6F3; border-radius: 999px; height: 10px; overflow: hidden; }
.dna-bar-fill { height: 10px; border-radius: 999px; }
.dna-style-tag {
  display: inline-flex; align-items: center; gap: .3rem;
  background: rgba(108,99,255,.1); color: var(--violet);
  border-radius: 999px; padding: .2rem .6rem;
  font-size: .78rem; font-weight: 600; margin: .15rem .15rem .15rem 0;
}
.dna-revision-item {
  border-left: 3px solid var(--coral);
  background: rgba(255,107,107,.07); border-radius: 8px;
  padding: .3rem .65rem; margin-bottom: .3rem;
  font-size: .85rem; color: var(--ink); font-weight: 500;
}
.dna-readiness-ring {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 2rem; font-weight: 700; color: var(--teal);
  text-align: center; padding: .6rem 0;
}

/* ── Exam Predictor ── */
.exam-hero {
  text-align: center;
  background: linear-gradient(135deg, #1E2233 0%, #2D3458 100%);
  border-radius: 20px; padding: 2rem 1.5rem; margin-bottom: 1.2rem;
  box-shadow: 0 8px 32px rgba(108,99,255,.25);
}
.exam-score-big {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 4rem; font-weight: 700; line-height: 1;
  background: linear-gradient(90deg, #6C63FF, #2EA8E0);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.exam-label {
  color: rgba(255,255,255,.6); font-size: .85rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: .08em;
}
.exam-confidence {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 1.3rem; font-weight: 600; color: #fff;
  margin-top: .3rem;
}
.exam-stat-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1rem 1.2rem; text-align: center;
}
.exam-stat-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 1.6rem; font-weight: 700; color: var(--violet);
}
.exam-stat-label { font-size: .78rem; color: var(--muted); font-weight: 500; margin-top: .15rem; }
.exam-weak-tag {
  display: inline-block; background: rgba(255,107,107,.12);
  color: #d84f4f; border-radius: 8px;
  padding: .3rem .75rem; margin: .2rem; font-size: .85rem; font-weight: 600;
}
.exam-star-topic {
  background: linear-gradient(90deg, rgba(108,99,255,.12), rgba(46,168,224,.12));
  border: 1px solid var(--border); border-radius: 12px;
  padding: .8rem 1rem; font-weight: 700; font-size: 1rem; color: var(--ink);
  text-align: center; margin-top: .5rem;
}

@media (max-width: 640px) {
  .sm-hero-title { font-size:1.6rem; }
  .sm-hero-tag { font-size:.85rem; }
  .sm-pill { font-size:.72rem; padding:.22rem .55rem; gap:.25rem; }
  .stTabs [data-baseweb="tab-list"] { gap:2px; overflow-x:auto; flex-wrap:nowrap; }
  .stTabs [data-baseweb="tab"] { padding:6px 10px; font-size:.82rem; white-space:nowrap; }
  .stButton > button, .stDownloadButton > button { min-height:44px; font-size:.9rem; }
  .sm-flashcard { padding:1.6rem 1rem; font-size:1.05rem; min-height:100px; }
  .sm-score-card { font-size:1.15rem; padding:.85rem 1rem; }
  [data-testid="stMetric"] { padding:.4rem .5rem; }
  [data-testid="stMetricValue"] { font-size:1.1rem !important; }
  .exam-score-big { font-size: 2.8rem; }
}
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


def render_progress_bar(label: str, pct: int, color: str = "#6C63FF"):
    """Render a labelled progress bar using HTML."""
    pct = max(0, min(100, pct))
    st.markdown(
        f"""
        <div class="dna-bar-wrap">
          <div class="dna-bar-label">{label}</div>
          <div class="dna-bar-bg">
            <div class="dna-bar-fill" style="width:{pct}%; background:{color};"></div>
          </div>
          <div style="font-size:.75rem; color:#6B7280; text-align:right; margin-top:2px;">{pct}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📚 Your Topics")
    if st.button("🔄 Refresh Topics", use_container_width=True):
        st.session_state.topics = run_async(get_topics())

    if "topics" not in st.session_state:
        st.session_state.topics = run_async(get_topics())

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
                        for key in ("quiz", "quiz_submitted", "flashcards", "card_index", "card_flipped", "study_plan", "kg_data", "dna_data", "exam_data"):
                            st.session_state.pop(key, None)
                        st.rerun()
                with cols[2]:
                    if st.button("🗑️", key=f"delete_{t['name']}", help=f"Delete topic {t['name']}"):
                        with st.spinner(f"Deleting {t['name']}..."):
                            result = run_async_safe(
                                delete_topic(t["name"]),
                                f"Couldn't delete '{t['name']}' right now."
                            )
                        if result:
                            st.toast(result)
                            st.session_state.topics = run_async(get_topics())
                            st.rerun()
    else:
        st.caption("No topics yet — add some notes to get started!")

    st.divider()
    if not memory.check_ollama_running():
        if memory.COGNEE_MODE == "cloud":
            st.warning("⚠️ Ollama isn't running. Cloud memory search will still work, but quiz/flashcard/study-plan generation needs Ollama locally.")
        else:
            st.error("⚠️ Ollama isn't running. Start it, or switch to Cloud (Cognee) mode in ⚙️ Settings.")

    # ── Study Progress ────────────────────────────────────────────────────────
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

    # ── 🧬 Learning DNA (replaces plain Weak Areas) ───────────────────────────
    st.subheader("🧬 Learning DNA")

    if "weak_areas" not in st.session_state:
        st.session_state.weak_areas = run_async_safe(
            get_weak_areas(),
            "Couldn't load weak areas right now."
        ) or []

    if "dna_sidebar" not in st.session_state:
        st.session_state.dna_sidebar = None

    if st.button("🔄 Refresh DNA Profile", use_container_width=True):
        with st.spinner("Analysing learning profile..."):
            dna = run_async_safe(
                get_learning_dna(st.session_state.get("dataset_name", "studymate")),
                "Couldn't refresh Learning DNA right now."
            )
        if dna:
            st.session_state.dna_sidebar = dna

    dna = st.session_state.dna_sidebar
    if dna:
        styles_html = "".join(
            f'<span class="dna-style-tag">✓ {s}</span>'
            for s in dna.get("learning_styles", [])
        )
        revisions_html = "".join(
            f'<div class="dna-revision-item">• {t}</div>'
            for t in dna.get("revision_topics", [])
        )
        knowledge_pct = dna.get("knowledge_pct", 50)
        confidence_pct = dna.get("confidence_pct", 50)
        readiness_pct = dna.get("exam_readiness_pct", 50)
        readiness_color = (
            "#12A594" if readiness_pct >= 75
            else "#F5A623" if readiness_pct >= 50
            else "#FF6B6B"
        )

        st.markdown(
            f"""
            <div class="dna-card">
              <div class="dna-title">Learning Style</div>
              <div style="margin-bottom:.7rem;">{styles_html}</div>
              <div class="dna-title" style="margin-top:.6rem;">Knowledge</div>
              <div class="dna-bar-wrap">
                <div class="dna-bar-bg">
                  <div class="dna-bar-fill" style="width:{knowledge_pct}%; background:#6C63FF;"></div>
                </div>
                <div style="font-size:.75rem;color:#6B7280;text-align:right;margin-top:2px;">{knowledge_pct}%</div>
              </div>
              <div class="dna-title" style="margin-top:.4rem;">Confidence</div>
              <div class="dna-bar-wrap">
                <div class="dna-bar-bg">
                  <div class="dna-bar-fill" style="width:{confidence_pct}%; background:#2EA8E0;"></div>
                </div>
                <div style="font-size:.75rem;color:#6B7280;text-align:right;margin-top:2px;">{confidence_pct}%</div>
              </div>
              <div class="dna-title" style="margin-top:.4rem;">Revision Needed</div>
              {revisions_html}
              <div class="dna-title" style="margin-top:.8rem;">Exam Readiness</div>
              <div class="dna-readiness-ring" style="color:{readiness_color};">{readiness_pct}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("Click 'Refresh DNA Profile' after adding notes!")

    st.divider()

    # ── Achievements ──────────────────────────────────────────────────────────
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


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="sm-hero-title">🧠 StudyMate AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-hero-tag">Your memory-powered study assistant</div>', unsafe_allow_html=True)

if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = "studymate"

st.session_state.dataset_name = st.text_input(
    "📌 Active topic:",
    value=st.session_state.dataset_name,
    help="All notes you add and questions you ask apply to this topic."
)
if not st.session_state.dataset_name.strip():
    st.session_state.dataset_name = "studymate"

dataset_name = st.session_state.dataset_name
clean_name = sanitize_name(dataset_name)

if not clean_name:
    st.warning("⚠️ Topic name can't be empty or symbols-only. Falling back to 'studymate'.")
    clean_name = "studymate"

if st.session_state.get("_last_clean_name") not in (None, clean_name):
    for key in ("quiz", "quiz_submitted", "flashcards", "card_index", "card_flipped", "study_plan", "kg_data", "dna_data", "exam_data"):
        st.session_state.pop(key, None)
st.session_state["_last_clean_name"] = clean_name

st.markdown(f'<span class="sm-pill sm-pill-violet">📖 Studying: {clean_name}</span>', unsafe_allow_html=True)

if clean_name != dataset_name:
    st.caption(f"⚠️ Topic will be saved as: `{clean_name}` (spaces/dots not allowed)")

st.divider()

tab_notes, tab_ask, tab_quiz, tab_flash, tab_plan, tab_kg, tab_exam, tab_settings = st.tabs(
    ["📄 Notes", "💬 Ask", "📝 Quiz", "🔁 Flashcards", "📅 Study Plan",
     "🕸️ Knowledge Graph", "🎯 Exam Predictor", "⚙️ Settings"]
)


def show_result(result: str):
    if result and result.strip().startswith("❌"):
        st.error(result)
    else:
        st.success(result)


def no_notes_banner():
    if not st.session_state.get("topics"):
        st.info("📄 You haven't added any notes yet — head to the **Notes** tab first so there's something to work with here.")


# ── Tab 1: Add Notes ──────────────────────────────────────────────────────────
with tab_notes:
    with st.container(border=True):
        st.subheader("Paste Notes")
        notes_input = st.text_area("Paste your notes here:", height=200)

        if st.button("📥 Save to Memory", use_container_width=True, type="primary"):
            if notes_input.strip():
                with st.spinner("Building knowledge graph... (this may take a few mins ⏳)"):
                    result = run_async_safe(
                        add_notes(notes_input, dataset_name),
                        "Couldn't save your notes right now."
                    )
                if result:
                    show_result(result)
                    st.session_state.topics = run_async(get_topics())
                    # Clear cached graph so it regenerates on next visit
                    st.session_state.pop("kg_data", None)
            else:
                st.warning("Please paste some notes first!")

    st.write("")

    with st.container(border=True):
        st.subheader("Upload PDF")
        pdf_file = st.file_uploader("Upload a PDF of your notes/textbook chapter:", type=["pdf"])

        if st.button("📥 Save PDF to Memory", use_container_width=True, type="primary"):
            if pdf_file is not None:
                pdf_text = ""
                extraction_ok = False
                try:
                    with st.spinner("Extracting text from PDF..."):
                        reader = PdfReader(pdf_file)
                        for page in reader.pages:
                            extracted = page.extract_text()
                            if extracted:
                                pdf_text += extracted + "\n"
                    extraction_ok = True
                except Exception as e:
                    st.error("⚠️ Couldn't read that PDF — it may be corrupted, password-protected, or in an unsupported format.")
                    with st.expander("Technical details"):
                        st.code(f"{type(e).__name__}: {e}")

                if extraction_ok and pdf_text.strip():
                    with st.spinner("Building knowledge graph from PDF... (this may take a few mins ⏳)"):
                        result = run_async_safe(
                            add_notes(pdf_text, dataset_name),
                            "Couldn't save the PDF notes right now."
                        )
                    if result:
                        show_result(result)
                        st.session_state.topics = run_async(get_topics())
                        st.session_state.pop("kg_data", None)
                elif extraction_ok:
                    st.warning("Couldn't extract text. It might be a scanned/image-based PDF.")
            else:
                st.warning("Please upload a PDF first!")


# ── Tab 2: Ask ────────────────────────────────────────────────────────────────
with tab_ask:
    no_notes_banner()
    with st.container(border=True):
        st.subheader("Ask a Question")
        question = st.text_input("What do you want to know?")

        difficulty = st.select_slider(
            "🎯 Difficulty level:",
            options=["Beginner", "Intermediate", "Advanced"],
            value="Intermediate"
        )
        st.caption("💡 Beginner = simple analogies | Intermediate = balanced | Advanced = technical depth")

        if st.button("🔍 Ask", use_container_width=True, type="primary"):
            if question.strip():
                with st.spinner("Building your learning profile for the first time — this can take a minute or two..." if memory._learning_profile_cache is None else "Searching memory and generating adaptive answer..."):
                    results = run_async_safe(
                        ask_question(question, dataset_name, difficulty),
                        "Couldn't generate an answer right now."
                    )
                if results is not None:
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


# ── Tab 3: Quiz ───────────────────────────────────────────────────────────────
with tab_quiz:
    no_notes_banner()
    with st.container(border=True):
        st.subheader("Quiz Me")
        num_q = st.slider("Number of questions:", min_value=3, max_value=10, value=5)

        if st.button("🎯 Generate Quiz", use_container_width=True, type="primary"):
            with st.spinner("Generating quiz from your notes..."):
                quiz = run_async_safe(
                    generate_quiz(dataset_name, num_q),
                    "Couldn't generate the quiz right now."
                )
            if quiz:
                st.session_state.quiz = quiz
                st.session_state.quiz_submitted = False
            elif quiz is not None:
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
                wrong_answers = []
                for i, q in enumerate(st.session_state.quiz):
                    selected_letter = user_answers[i].strip()[0].upper() if user_answers[i].strip() else ""
                    correct = q["correct_answer"].strip()[0].upper()
                    if selected_letter == correct:
                        score += 1
                        st.success(f"Q{i+1}: Correct! ✅")
                    else:
                        st.error(f"Q{i+1}: Incorrect ❌ — Correct answer: {correct}")
                        wrong_answers.append({
                            "question": q["question"],
                            "correct_answer": correct,
                            "user_answer": selected_letter
                        })

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

                if wrong_answers:
                    with st.spinner("Saving your weak areas to memory..."):
                        run_async_safe(
                            save_struggles_batch(dataset_name, wrong_answers),
                            "Your score was recorded, but saving weak areas to memory failed."
                        )
                    st.session_state.weak_areas = run_async(get_weak_areas())
                    # Invalidate exam/dna caches so they regenerate fresh
                    st.session_state.pop("exam_data", None)
                    st.session_state.pop("dna_sidebar", None)


# ── Tab 4: Flashcards ─────────────────────────────────────────────────────────
with tab_flash:
    no_notes_banner()
    with st.container(border=True):
        st.subheader("🔁 Flashcards")
        num_cards = st.slider("Number of flashcards:", min_value=3, max_value=15, value=5)

        if st.button("✨ Generate Flashcards", use_container_width=True, type="primary"):
            with st.spinner("Generating flashcards from your notes..."):
                cards = run_async_safe(
                    generate_flashcards(dataset_name, num_cards),
                    "Couldn't generate flashcards right now."
                )
            if cards:
                st.session_state.flashcards = cards
                st.session_state.card_index = 0
                st.session_state.card_flipped = False
            elif cards is not None:
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


# ── Tab 5: Study Plan ─────────────────────────────────────────────────────────
with tab_plan:
    no_notes_banner()
    with st.container(border=True):
        st.subheader("📅 AI Study Plan")
        days = st.slider("Plan duration (days):", min_value=3, max_value=14, value=7)

        if st.button("🧠 Generate Study Plan", use_container_width=True, type="primary"):
            with st.spinner("Generating your personalized study plan..."):
                plan = run_async_safe(
                    generate_study_plan(dataset_name, days),
                    "Couldn't generate a study plan right now."
                )
            if plan:
                st.session_state.study_plan = plan
            elif plan is not None:
                st.warning("Couldn't generate a study plan. Add some notes first!")

    if "study_plan" in st.session_state and st.session_state.study_plan:
        st.write("")
        for day in st.session_state.study_plan:
            with st.expander(f"📅 Day {day['day']} — {day['focus']}"):
                for task in day["tasks"]:
                    st.write(f"• {task}")
                st.info(f"💡 Tip: {day['tip']}")


# ── Tab 6: 🕸️ Knowledge Graph ─────────────────────────────────────────────────
with tab_kg:
    no_notes_banner()
    st.markdown(
        '<span class="sm-pill sm-pill-violet">🕸️ AI-extracted concept map from your notes</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    col_gen, col_clear = st.columns([3, 1])
    with col_gen:
        gen_kg = st.button("🔍 Generate Knowledge Graph", use_container_width=True, type="primary")
    with col_clear:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.pop("kg_data", None)
            st.rerun()

    if gen_kg:
        with st.spinner("Extracting concepts and relationships from your notes... ⏳"):
            kg = run_async_safe(
                get_knowledge_graph(dataset_name),
                "Couldn't generate the knowledge graph right now."
            )
        if kg and kg.get("nodes"):
            st.session_state.kg_data = kg
        elif kg is not None:
            st.warning("No concepts found. Make sure you have added notes for this topic first!")

    if st.session_state.get("kg_data"):
        kg = st.session_state.kg_data
        nodes = kg.get("nodes", [])
        edges = kg.get("edges", [])

        if nodes:
            st.success(f"✅ Extracted **{len(nodes)} concepts** and **{len(edges)} relationships** automatically from your notes.")

            # Build PyVis interactive graph
            try:
                from pyvis.network import Network
                import networkx as nx

                G = nx.DiGraph()
                G.add_nodes_from(nodes)
                for e in edges:
                    if e.get("from") in nodes and e.get("to") in nodes:
                        G.add_edge(e["from"], e["to"], title=e.get("label", ""))

                net = Network(
                    height="520px",
                    width="100%",
                    bgcolor="#FBFBFE",
                    font_color="#1E2233",
                    directed=True,
                )
                net.from_nx(G)

                # Style nodes
                for node in net.nodes:
                    node["color"] = {
                        "background": "#EAF0FF",
                        "border": "#6C63FF",
                        "highlight": {"background": "#6C63FF", "border": "#3D35CC"},
                    }
                    node["font"] = {"size": 15, "face": "Inter", "color": "#1E2233"}
                    node["size"] = 28
                    node["shape"] = "dot"

                # Style edges
                for edge in net.edges:
                    edge["color"] = {"color": "#2EA8E0", "highlight": "#6C63FF"}
                    edge["font"] = {"size": 11, "color": "#6B7280", "face": "Inter"}
                    edge["arrows"] = "to"
                    edge["smooth"] = {"type": "curvedCW", "roundness": 0.2}

                net.set_options("""
                {
                  "physics": {
                    "enabled": true,
                    "barnesHut": {
                      "gravitationalConstant": -8000,
                      "centralGravity": 0.3,
                      "springLength": 140,
                      "springConstant": 0.04,
                      "damping": 0.09
                    }
                  },
                  "interaction": {
                    "hover": true,
                    "tooltipDelay": 100,
                    "zoomView": true,
                    "dragView": true
                  }
                }
                """)

                html_str = net.generate_html()
                components.html(html_str, height=540, scrolling=False)

            except ImportError:
                # Fallback: plain NetworkX text representation
                st.info("PyVis not available — showing text representation instead.")
                st.markdown("**Nodes (Concepts):**")
                for n in nodes:
                    st.markdown(f"- `{n}`")
                st.markdown("**Edges (Relationships):**")
                for e in edges:
                    st.markdown(f"- **{e.get('from')}** → *{e.get('label', '→')}* → **{e.get('to')}**")

            # Text summary below graph
            with st.expander("📋 Concept list", expanded=False):
                cols = st.columns(3)
                for i, node in enumerate(nodes):
                    cols[i % 3].markdown(
                        f'<span class="sm-pill sm-pill-violet">{node}</span>',
                        unsafe_allow_html=True,
                    )
                st.write("")
                st.markdown("**Relationships:**")
                for e in edges:
                    st.markdown(f"• **{e.get('from')}** *{e.get('label', '→')}* **{e.get('to')}**")

        else:
            st.warning("The AI couldn't extract any concepts. Try adding more detailed notes first.")
    else:
        st.info("👆 Click **Generate Knowledge Graph** to visualise the concepts extracted from your notes.")


# ── Tab 7: 🎯 Exam Predictor ──────────────────────────────────────────────────
with tab_exam:
    no_notes_banner()

    st.markdown(
        '<span class="sm-pill sm-pill-sky">🎯 AI-powered exam performance prediction</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    col_pred, col_clr = st.columns([3, 1])
    with col_pred:
        run_prediction = st.button("🔮 Predict My Exam Score", use_container_width=True, type="primary")
    with col_clr:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.pop("exam_data", None)
            st.rerun()

    if run_prediction:
        with st.spinner("Analysing your notes and quiz history to predict your exam performance..."):
            prediction = run_async_safe(
                predict_exam(dataset_name),
                "Couldn't generate the exam prediction right now."
            )
        if prediction:
            st.session_state.exam_data = prediction

    if st.session_state.get("exam_data"):
        p = st.session_state.exam_data
        exp_score = p.get("expected_score_pct", 0)
        conf = p.get("confidence_pct", 0)
        weak_topics = p.get("weak_topics", [])
        rev_hours = p.get("estimated_revision_hours", 0)
        top_topic = p.get("most_important_topic", "")

        # Hero score panel
        score_grade = "🟢" if exp_score >= 80 else "🟡" if exp_score >= 60 else "🔴"
        st.markdown(
            f"""
            <div class="exam-hero">
              <div class="exam-label">Expected Score</div>
              <div class="exam-score-big">{exp_score}%</div>
              <div class="exam-confidence">{score_grade} Prediction confidence: {conf}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Stats row
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="exam-stat-card">
                  <div class="exam-stat-value">{rev_hours}h</div>
                  <div class="exam-stat-label">Estimated Revision</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="exam-stat-card">
                  <div class="exam-stat-value">{len(weak_topics)}</div>
                  <div class="exam-stat-label">Weak Topics</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="exam-stat-card">
                  <div class="exam-stat-value">{conf}%</div>
                  <div class="exam-stat-label">Confidence</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # Weak topics
        with st.container(border=True):
            st.markdown("#### ⚠️ Weak Topics to Focus On")
            weak_html = "".join(
                f'<span class="exam-weak-tag">⚠️ {t}</span>' for t in weak_topics
            )
            st.markdown(weak_html, unsafe_allow_html=True)

        st.write("")

        # Most important topic
        with st.container(border=True):
            st.markdown("#### 🔥 Most Important Topic Right Now")
            st.markdown(
                f'<div class="exam-star-topic">⭐ {top_topic}</div>',
                unsafe_allow_html=True,
            )

        st.write("")

        # Revision progress bars
        with st.container(border=True):
            st.markdown("#### 📊 Readiness Breakdown")
            render_progress_bar("Expected Score", exp_score, "#6C63FF")
            render_progress_bar("Prediction Confidence", conf, "#2EA8E0")
            remaining = max(0, 100 - exp_score)
            render_progress_bar("Gap to Close", remaining, "#FF6B6B")

        # Advice
        st.write("")
        if exp_score >= 80:
            st.success("🎉 You're well-prepared! Keep revising your weak topics for an even better score.")
        elif exp_score >= 60:
            st.warning(f"📚 You're on track — focus your revision on **{top_topic}** and the weak topics above.")
        else:
            st.error(f"⚡ Intensive revision needed. Start with **{top_topic}** and work through each weak area systematically.")

    else:
        st.info("👆 Click **Predict My Exam Score** to get your AI-powered performance forecast based on your notes and quiz history.")


# ── Tab 8: Settings ───────────────────────────────────────────────────────────
with tab_settings:
    with st.container(border=True):
        st.subheader("Settings")
        st.markdown(f'<span class="sm-pill sm-pill-slate">📖 Current active topic: {clean_name}</span>', unsafe_allow_html=True)

        st.write("")
        st.subheader("Memory Backend")
        backend_choice = st.radio(
            "Choose where StudyMate AI stores memory:",
            ["Local (Ollama)", "Cloud (Cognee)"],
            key="backend_choice"
        )
        if backend_choice == "Cloud (Cognee)":
            memory.set_mode("cloud")
            if not memory.COGNEE_API_KEY or not memory.COGNEE_API_KEY:
                st.warning("⚠️ Cloud credentials not set! Add COGNEE_BASE_URL and COGNEE_API_KEY to your .env file.")
            else:
                st.success("Using Cognee Cloud for memory")
        else:
            memory.set_mode("local")
            st.info("ℹ️ Using local Ollama pipeline")

        st.write("")
        if st.button("🔄 Refresh Learning Profile", use_container_width=True):
            memory._learning_profile_cache = None
            st.session_state.pop("dna_sidebar", None)
            st.session_state.pop("exam_data", None)
            st.success("Learning profile will refresh on your next question.")

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
                    result = run_async_safe(
                        delete_topic(topic_to_delete),
                        f"Couldn't delete '{topic_to_delete}' right now."
                    )
                if result:
                    show_result(result)
                    st.session_state.topics = run_async(get_topics())
                    st.rerun()
        else:
            st.caption("No topics to delete yet!")

    st.write("")

    with st.container(border=True):
        st.warning("This will permanently delete all stored notes and knowledge graphs.")
        if st.button("🗑️ Clear All Memory", use_container_width=True):
            with st.spinner("Clearing..."):
                result = run_async_safe(
                    reset_memory(),
                    "Couldn't clear memory right now."
                )
            if result:
                show_result(result)
                st.session_state.topics = []
                st.session_state.weak_areas = []
                st.session_state.quiz_scores = []
                st.session_state.study_plan = []
                st.session_state.pop("kg_data", None)
                st.session_state.pop("dna_sidebar", None)
                st.session_state.pop("exam_data", None)
