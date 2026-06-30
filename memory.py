import ollama
import cognee
import json
from cognee.api.v1.search import SearchType
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def setup_cognee():
    cognee.config.set_llm_config({
        "llm_provider": "ollama",
        "llm_model": "qwen2.5:7b",
        "llm_endpoint": "http://localhost:11434/v1",
        "llm_api_key": "ollama"
    })
    cognee.config.set_embedding_config({
        "embedding_provider": "ollama",
        "embedding_model": "nomic-embed-text",
        "embedding_endpoint": "http://localhost:11434/api/embed",
        "embedding_api_key": "ollama"
    })

async def add_notes(text: str, dataset_name: str = "studymate"):
    await setup_cognee()
    await cognee.add(text, dataset_name=dataset_name)
    await cognee.cognify([dataset_name])
    return "✅ Notes added and indexed into memory!"

async def ask_question(question: str, dataset_name: str = "studymate"):
    await setup_cognee()
    results = await cognee.search(
        query_text=question,
        query_type=SearchType.GRAPH_COMPLETION,
        datasets=[dataset_name]
    )
    return results

async def generate_quiz(dataset_name: str = "studymate", num_questions: int = 5):
    await setup_cognee()

    summary_results = await cognee.search(
        query_text="Summarize all the key concepts, facts, and topics covered in these notes.",
        query_type=SearchType.GRAPH_COMPLETION,
        datasets=[dataset_name]
    )

    summary_text = ""
    for r in summary_results:
        if isinstance(r, dict) and "search_result" in r:
            summary_text += " ".join(r["search_result"]) + " "
        else:
            summary_text += str(r) + " "

    if not summary_text.strip():
        return []

    prompt = f"""Based on the following study material summary, create {num_questions} multiple-choice quiz questions to test understanding.

Study material:
{summary_text}

Return ONLY valid JSON in this exact format, nothing else:
[
  {{
    "question": "...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A"
  }}
]"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        quiz = json.loads(raw)
        return quiz
    except json.JSONDecodeError:
        return []

async def get_topics():
    try:
        await setup_cognee()
        datasets = await cognee.datasets.list_datasets()
        topics = []
        for ds in datasets:
            topics.append({
                "name": ds.name,
                "updated_at": getattr(ds, "updated_at", None),
            })
        topics.sort(key=lambda t: t["updated_at"] or "", reverse=True)
        return topics
    except Exception:
        # No database exists yet (e.g. fresh install, no notes added yet)
        return []

async def reset_memory():
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    return "🗑️ Memory cleared!"