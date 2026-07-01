# 🧠 StudyMate AI

> **Your memory-powered, adaptive study assistant — built with Cognee, Ollama, and Streamlit.**

Built for the **WeMakeDevs x Cognee Hackathon** 🏆

---

## ✨ What is StudyMate AI?

StudyMate AI is a local, privacy-first study assistant that learns *with* you. Upload your notes or PDFs, ask questions, take quizzes — and watch it adapt to how you learn best over time using **Cognee's knowledge graph memory**.

No cloud. No API keys. Runs entirely on your machine.

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 📄 **Notes & PDF Upload** | Paste notes or upload a PDF and store them in Cognee's knowledge graph |
| 💬 **Adaptive Q&A** | Ask questions — answers are generated from *your notes*, not random internet data |
| 🎯 **Difficulty Modes** | Choose Beginner, Intermediate, or Advanced answer style |
| 📝 **AI Quiz Generator** | Auto-generates multiple-choice quizzes from your notes |
| 🔁 **Flashcard Mode** | Interactive flip cards generated from your study material |
| 📅 **AI Study Plan** | Personalized day-by-day study plan based on your notes and weak areas |
| 🕸️ **Knowledge Graph Visualizer** | Interactive visual graph of how concepts in your notes connect |
| ⚠️ **Weak Areas Tracker** | Tracks quiz mistakes and highlights what needs more revision |
| 📊 **Study Progress Dashboard** | Quizzes taken, average score, best score — all in the sidebar |
| 🏅 **Achievements & Badges** | Earn badges as you study more (First Quiz, Perfect Score, Brain Power...) |
| 📚 **Topics Sidebar** | All your study topics in one place — switch between them instantly |
| 🗑️ **Delete Topics** | Remove topics you've mastered or no longer need |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Cognee](https://github.com/topoteretes/cognee) | Memory layer — stores notes as a knowledge graph |
| [Ollama](https://ollama.com) | Local LLM runner |
| [qwen2.5:7b](https://ollama.com/library/qwen2.5) | Primary LLM for Q&A, quiz, flashcards, study plan |
| [nomic-embed-text](https://ollama.com/library/nomic-embed-text) | Embeddings for semantic search |
| [Streamlit](https://streamlit.io) | Web UI |
| [pypdf](https://pypdf.readthedocs.io) | PDF text extraction |
| [vis.js](https://visjs.org) | Knowledge graph visualization |
| Python | Backend logic |

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running

### 1. Clone the repo

```bash
git clone https://github.com/Darshan-coder-sru/studymate-ai.git
cd studymate-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Pull required Ollama models

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### 4. Make sure Ollama is running

```bash
ollama serve
```

> If you see `bind: Only one usage of each socket address` — Ollama is already running. That's fine!

### 5. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` 🎉

---

## 🔧 Configuration

Create a `.env` file in the project root (optional):

```env
OLLAMA_BASE_URL=http://localhost:11434
```

All other config is handled automatically in `memory.py`.

---

## 📁 Project Structure

```
studymate-ai/
├── app.py          # Streamlit UI — all tabs, sidebar, interactions
├── memory.py       # Cognee memory layer — all AI logic
├── .env            # Optional environment variables
├── .streamlit      # For better UI and clean interface 
├── README.md
└── requirements.txt 

```

---

## 🎮 How to Use

1. **Add Notes** — Paste your study notes or upload a PDF in the Notes tab
2. **Ask Questions** — Switch to the Ask tab, type your question, pick a difficulty
3. **Take a Quiz** — Go to Quiz tab, generate questions, submit and get scored
4. **Review Flashcards** — Generate and flip through cards in the Flashcards tab
5. **Get a Study Plan** — Generate a personalized day-by-day plan in the Study Plan tab
6. **Visualize Concepts** — See how ideas connect in the Knowledge Graph tab
7. **Track Progress** — Check the sidebar for your scores, weak areas, and achievements

---

## 🧠 How Cognee Powers StudyMate AI

StudyMate AI uses Cognee as its **persistent memory layer**:

- When you add notes → Cognee builds a **knowledge graph** from your text
- When you ask a question → Cognee does a **graph completion search** to find relevant context
- When you get a question wrong → The mistake is **stored back into Cognee** as a struggle note
- When you ask again → Cognee retrieves your **learning profile** and adapts the answer

This means StudyMate AI genuinely gets smarter the more you use it — it remembers what you've studied, what you've struggled with, and how you learn best.

---

## 🗺️ Roadmap

- [ ] Cognee Cloud integration
- [ ] Multi-language answer support
- [ ] Export quiz as PDF
- [ ] Voice input support
- [ ] Topic mastery score (0–100%)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙌 Acknowledgements

- [Cognee](https://github.com/topoteretes/cognee) — for the incredible knowledge graph memory layer
- [WeMakeDevs](https://wemakedevs.org) — for organizing the hackathon
- [Ollama](https://ollama.com) — for making local LLMs accessible

---

<p align="center">Built with ❤️ by Darshan for the WeMakeDevs x Cognee Hackathon</p>
