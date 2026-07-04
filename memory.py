import os
import re

os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_MODEL"] = "qwen2.5:7b"
os.environ["LLM_ENDPOINT"] = "http://localhost:11434/v1"
os.environ["LLM_API_KEY"] = "ollama"
os.environ["EMBEDDING_PROVIDER"] = "ollama"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text"
os.environ["EMBEDDING_ENDPOINT"] = "http://localhost:11434/api/embed"
os.environ["EMBEDDING_DIMENSIONS"] = "768"
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"
os.environ["TELEMETRY_DISABLED"] = "true"

import ollama
import cognee
import json
import requests
from cognee.api.v1.search import SearchType
import asyncio
from dotenv import load_dotenv

load_dotenv()

_learning_profile_cache = None

COGNEE_MODE = "local"

def set_mode(mode: str):
    global COGNEE_MODE
    COGNEE_MODE = mode

COGNEE_BASE_URL = os.environ.get("COGNEE_BASE_URL", "")
COGNEE_API_KEY = os.environ.get("COGNEE_API_KEY", "")
COGNEE_TENANT_ID = os.environ.get("COGNEE_TENANT_ID", "")

def check_ollama_running():
    try:
        import requests
        resp = requests.get("http://localhost:11434", timeout=3)
        return True
    except Exception:
        return False

def _cloud_headers():
    return {
        "X-Api-Key": COGNEE_API_KEY,
        "X-Tenant-Id": COGNEE_TENANT_ID,
        "Content-Type": "application/json"
    }

def cloud_add(text: str, dataset_name: str):
    resp = requests.post(
        f"{COGNEE_BASE_URL}/api/v1/add",
        json={"data": text, "datasetName": dataset_name},
        headers=_cloud_headers()
    )
    resp.raise_for_status()

def cloud_cognify(dataset_name: str):
    resp = requests.post(
        f"{COGNEE_BASE_URL}/api/v1/cognify",
        json={"datasets": [dataset_name]},
        headers=_cloud_headers()
    )
    resp.raise_for_status()

def cloud_search(query_text: str, dataset_name: str = None):
    payload = {"query": query_text, "searchType": "CHUNKS"}
    if dataset_name:
        payload["datasets"] = [dataset_name]
    resp = requests.post(
        f"{COGNEE_BASE_URL}/api/v1/search",
        json=payload,
        headers=_cloud_headers()
    )
    resp.raise_for_status()
    return resp.json()


def cloud_list_datasets():
    resp = requests.get(
        f"{COGNEE_BASE_URL}/api/v1/datasets",
        headers=_cloud_headers()
    )
    resp.raise_for_status()
    return resp.json()


def cloud_delete_dataset(dataset_id: str):
    resp = requests.delete(
        f"{COGNEE_BASE_URL}/api/v1/datasets/{dataset_id}",
        headers=_cloud_headers()
    )
    resp.raise_for_status()


def sanitize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())


def _chat_content(response) -> str:
    try:
        return response.message.content
    except AttributeError:
        pass
    if isinstance(response, dict):
        return response.get("message", {}).get("content", "")
    return str(response)


def safe_ollama_chat(prompt: str) -> str:
    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
        )
        return _chat_content(response)
    except Exception as e:
        print(f"[Ollama] Chat call failed: {e}")
        return ""


def parse_json_response(raw: str):
    if not raw:
        return []

    raw = raw.strip()

    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            candidate = parts[1]
            if candidate.startswith("json"):
                candidate = candidate[4:]
            raw = candidate.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\[.*\]|\{.*\})", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    print("[JSON] Could not parse model output as JSON.")
    return []


async def setup_cognee():
    try:
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
    except Exception:
        pass


def extract_text(results):
    parts = []
    for r in results:
        if isinstance(r, dict) and "search_result" in r:
            sr = r["search_result"]
            if isinstance(sr, list):
                parts.append(" ".join(str(s) for s in sr))
            else:
                parts.append(str(sr))
        else:
            parts.append(str(r))
    return "\n".join(parts)


async def add_notes(text: str, dataset_name: str = "studymate"):
    dataset_name = sanitize_name(dataset_name)

    if COGNEE_MODE == "cloud":
        try:
            await asyncio.to_thread(cloud_add, text, dataset_name)
            await asyncio.to_thread(cloud_cognify, dataset_name)
            return "✅ Notes added and indexed into Cognee Cloud!"
        except Exception as e:
            print(f"[AddNotes] Cloud add/cognify failed: {e}")
            return f"❌ Failed to save notes to Cognee Cloud: {e}"

    try:
        await setup_cognee()
        await cognee.add(text, dataset_name=dataset_name)
        await cognee.cognify([dataset_name])
        return "✅ Notes added and indexed into memory!"
    except Exception as e:
        print(f"[AddNotes] Local add/cognify failed: {e}")
        return f"❌ Failed to save notes locally: {e}"


async def ask_question(question: str, dataset_name: str = "studymate", difficulty: str = "Intermediate"):
    dataset_name = sanitize_name(dataset_name)
    await setup_cognee()

    global _learning_profile_cache

    learning_profile_query = (
        "What learning style, analogies, or explanations has worked well "
        "for this student in the past? What topics have they struggled with? "
        "What questions did they answer incorrectly in quizzes?"
    )

    async def fetch_topic():
        try:
            if COGNEE_MODE == "cloud":
                results = await asyncio.to_thread(cloud_search, question, dataset_name)
            else:
                results = await cognee.search(
                    query_text=question,
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=[dataset_name],
                )
            return results
        except Exception as e:
            print(f"[AdaptiveAsk] Topic search failed: {e}")
            return []

    async def fetch_profile():
        global _learning_profile_cache
        if _learning_profile_cache is not None:
            return _learning_profile_cache
        try:
            if COGNEE_MODE == "cloud":
                results = await asyncio.to_thread(cloud_search, learning_profile_query)
            else:
                results = await cognee.search(
                    query_text=learning_profile_query,
                    query_type=SearchType.GRAPH_COMPLETION,
                )
            _learning_profile_cache = results
            return results
        except Exception as e:
            print(f"[AdaptiveAsk] No cross-topic memory yet: {e}")
            return []

    topic_results, profile_results = await asyncio.gather(
        fetch_topic(),
        fetch_profile()
    )

    topic_context = extract_text(topic_results)
    learning_profile_context = extract_text(profile_results)

    difficulty_instructions = {
        "Beginner": "Use very simple language, relatable analogies, and real-world examples. Avoid jargon.",
        "Intermediate": "Use clear explanations with some technical detail. Balance simplicity and depth.",
        "Advanced": "Use precise technical language, go deep into the concept, assume strong prior knowledge."
    }
    difficulty_note = difficulty_instructions.get(difficulty, difficulty_instructions["Intermediate"])

    if learning_profile_context:
        prompt = f"""You are StudyMate AI, a personalized study assistant.

A student is asking: "{question}"

--- Relevant notes from their study material on this topic ---
{topic_context or "No specific notes found for this topic yet."}

--- Learning profile: how this student learns best (from past sessions) ---
{learning_profile_context}

--- Difficulty level requested: {difficulty} ---
{difficulty_note}

Instructions:
- Answer the student question clearly and accurately.
- If relevant, reference how this topic connects to things they already know or struggled with.
- Use a similar explanation style that has worked well for them previously.
- Match the difficulty level strictly.
- Keep the answer focused and easy to understand.
"""
    else:
        prompt = f"""You are StudyMate AI, a personalized study assistant.

A student is asking: "{question}"

--- Relevant notes from their study material ---
{topic_context or "No specific notes found for this topic yet."}

--- Difficulty level requested: {difficulty} ---
{difficulty_note}

Instructions:
- Answer the student question clearly and accurately.
- Match the difficulty level strictly.
- Keep the answer focused and easy to understand.
"""

    answer = safe_ollama_chat(prompt)
    if not answer:
        answer = (
            "Could not generate an answer right now — the local model "
            "(Ollama) may not be running.\n\n"
            f"Here is the raw context from your notes:\n{topic_context or 'None found.'}"
        )

    return [{"search_result": [answer]}]


async def save_struggle(dataset_name: str, question: str, correct_answer: str, user_answer: str):
    dataset_name = sanitize_name(dataset_name)
    struggle_note = (
        f"The student answered '{user_answer}' but the correct answer was '{correct_answer}' "
        f"for the question: '{question}'. This is a weak area that needs more revision."
    )

    if COGNEE_MODE == "cloud":
        try:
            await asyncio.to_thread(cloud_add, struggle_note, "struggle_history")
            await asyncio.to_thread(cloud_cognify, "struggle_history")
        except Exception as e:
            print(f"[SaveStruggle] Cloud add/cognify failed: {e}")
        return struggle_note

    await setup_cognee()
    try:
        await cognee.add(struggle_note, dataset_name="struggle_history")
        await cognee.cognify(["struggle_history"])
    except Exception as e:
        print(f"[SaveStruggle] Local add/cognify failed: {e}")
    return struggle_note


async def save_struggles_batch(dataset_name: str, struggles: list):
    dataset_name = sanitize_name(dataset_name)
    if not struggles:
        return ""

    notes = [
        f"The student answered '{s['user_answer']}' but the correct answer was "
        f"'{s['correct_answer']}' for the question: '{s['question']}'. "
        f"This is a weak area that needs more revision."
        for s in struggles
    ]
    combined_note = "\n".join(notes)

    if COGNEE_MODE == "cloud":
        try:
            await asyncio.to_thread(cloud_add, combined_note, "struggle_history")
            await asyncio.to_thread(cloud_cognify, "struggle_history")
        except Exception as e:
            print(f"[SaveStrugglesBatch] Cloud add/cognify failed: {e}")
        return combined_note

    await setup_cognee()
    try:
        await cognee.add(combined_note, dataset_name="struggle_history")
        await cognee.cognify(["struggle_history"])
    except Exception as e:
        print(f"[SaveStrugglesBatch] Local add/cognify failed: {e}")
    return combined_note


async def get_weak_areas():
    query_text = "What topics and questions has the student struggled with or answered incorrectly?"
    try:
        if COGNEE_MODE == "cloud":
            results = await asyncio.to_thread(cloud_search, query_text, "struggle_history")
        else:
            await setup_cognee()
            results = await cognee.search(
                query_text=query_text,
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=["struggle_history"]
            )
        parts = []
        for r in results:
            if isinstance(r, dict) and "search_result" in r:
                parts.extend(r["search_result"])
            else:
                parts.append(str(r))
        return parts
    except Exception:
        import traceback
        traceback.print_exc()
        return []


async def _get_summary_text(query_text: str, dataset_name: str) -> str:
    if COGNEE_MODE == "cloud":
        try:
            results = await asyncio.to_thread(cloud_search, query_text, dataset_name)
        except Exception as e:
            print(f"[Summary] Cloud search failed: {e}")
            results = []
    else:
        await setup_cognee()
        try:
            results = await cognee.search(
                query_text=query_text,
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=[dataset_name]
            )
        except Exception as e:
            print(f"[Summary] Local search failed: {e}")
            results = []
    return extract_text(results)


def _valid_quiz_item(q) -> bool:
    if not (
        isinstance(q, dict)
        and isinstance(q.get("question"), str) and q["question"].strip()
        and isinstance(q.get("options"), list) and len(q["options"]) >= 2
        and isinstance(q.get("correct_answer"), str) and q["correct_answer"].strip()
    ):
        return False

    option_letters = []
    for opt in q["options"]:
        if not isinstance(opt, str) or not re.match(r"^[A-Za-z]\)", opt.strip()):
            return False
        option_letters.append(opt.strip()[0].upper())

    correct = q["correct_answer"].strip()[0].upper()
    return correct in option_letters


async def generate_quiz(dataset_name: str = "studymate", num_questions: int = 5):
    dataset_name = sanitize_name(dataset_name)

    summary_text = await _get_summary_text(
        "Summarize all the key concepts, facts, and topics covered in these notes.",
        dataset_name
    )

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

    raw = safe_ollama_chat(prompt)
    result = parse_json_response(raw)
    if not isinstance(result, list):
        return []

    valid = [q for q in result if _valid_quiz_item(q)]
    if len(valid) < len(result):
        print(f"[Quiz] Dropped {len(result) - len(valid)} malformed question(s) from model output.")
    return valid


async def generate_flashcards(dataset_name: str = "studymate", num_cards: int = 5):
    dataset_name = sanitize_name(dataset_name)

    summary_text = await _get_summary_text(
        "Summarize all the key concepts, terms, and definitions in these notes. "
        "Include as many distinct facts, terms, and ideas as possible.",
        dataset_name
    )

    if not summary_text.strip():
        return []

    prompt = f"""Based on the following study material, create EXACTLY {num_cards} flashcards.

Rules:
- You MUST return EXACTLY {num_cards} items in the JSON array — no more, no less.
- Each flashcard must cover a DIFFERENT concept or term.
- Front: a short question or term (max 15 words).
- Back: a clear answer or definition (max 40 words).
- Do NOT repeat similar cards.

Study material:
{summary_text}

Return ONLY valid JSON in this exact format, absolutely nothing else before or after:
[
  {{
    "front": "What is ...?",
    "back": "It is ..."
  }},
  {{
    "front": "Define ...",
    "back": "... is defined as ..."
  }}
]

IMPORTANT: The array must contain EXACTLY {num_cards} objects."""

    raw = safe_ollama_chat(prompt)
    result = parse_json_response(raw)

    if isinstance(result, list) and 0 < len(result) < num_cards:
        while len(result) < num_cards:
            result.append({
                "front": f"Card {len(result) + 1}: Review your notes",
                "back": "Add more detailed notes to generate more flashcards on this topic!"
            })
    elif isinstance(result, list) and len(result) > num_cards:
        result = result[:num_cards]

    return result if isinstance(result, list) else []


def _valid_plan_day(d) -> bool:
    return (
        isinstance(d, dict)
        and "day" in d
        and isinstance(d.get("focus"), str) and d["focus"].strip()
        and isinstance(d.get("tasks"), list)
        and isinstance(d.get("tip"), str)
    )


async def generate_study_plan(dataset_name: str = "studymate", days: int = 7):
    dataset_name = sanitize_name(dataset_name)

    async def fetch_notes_summary():
        return await _get_summary_text(
            "Summarize all key concepts and topics in these notes.",
            dataset_name
        )

    async def fetch_struggles():
        try:
            if COGNEE_MODE == "cloud":
                results = await asyncio.to_thread(
                    cloud_search, "What has the student struggled with?", "struggle_history"
                )
            else:
                results = await cognee.search(
                    query_text="What has the student struggled with?",
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=["struggle_history"]
                )
            return extract_text(results)
        except Exception:
            return ""

    notes_text, struggle_text = await asyncio.gather(
        fetch_notes_summary(),
        fetch_struggles()
    )

    if not notes_text.strip():
        return []

    prompt = f"""You are StudyMate AI. Create a personalized {days}-day study plan for a student.

Their notes cover:
{notes_text}

Their weak areas and struggles:
{struggle_text or "No struggles recorded yet."}

Return ONLY valid JSON in this exact format, nothing else:
[
  {{
    "day": 1,
    "focus": "Topic to focus on",
    "tasks": ["Task 1", "Task 2", "Task 3"],
    "tip": "A motivational or practical tip for the day"
  }}
]"""

    raw = safe_ollama_chat(prompt)
    result = parse_json_response(raw)
    if not isinstance(result, list):
        return []

    valid = [d for d in result if _valid_plan_day(d)]
    if len(valid) < len(result):
        print(f"[StudyPlan] Dropped {len(result) - len(valid)} malformed day(s) from model output.")
    return valid


async def delete_topic(dataset_name: str):
    dataset_name = sanitize_name(dataset_name)
    try:
        if COGNEE_MODE == "cloud":
            datasets = await asyncio.to_thread(cloud_list_datasets)
            match = next((ds for ds in datasets if ds["name"] == dataset_name), None)
            if match is None:
                return f"⚠️ Topic '{dataset_name}' not found."
            await asyncio.to_thread(cloud_delete_dataset, match["id"])
            return f"✅ Topic '{dataset_name}' deleted successfully!"

        await setup_cognee()
        datasets = await cognee.datasets.list_datasets()
        match = next((ds for ds in datasets if ds.name == dataset_name), None)
        if match is None:
            return f"⚠️ Topic '{dataset_name}' not found."
        await cognee.datasets.empty_dataset(dataset_id=match.id)
        return f"✅ Topic '{dataset_name}' deleted successfully!"
    except Exception as e:
        return f"❌ Could not delete topic: {e}"


async def get_topics():
    try:
        if COGNEE_MODE == "cloud":
            datasets = await asyncio.to_thread(cloud_list_datasets)
            topics = [
                {"name": ds["name"], "updated_at": ds.get("updatedAt")}
                for ds in datasets
            ]
        else:
            await setup_cognee()
            raw_datasets = await cognee.datasets.list_datasets()
            topics = [
                {"name": ds.name, "updated_at": getattr(ds, "updated_at", None)}
                for ds in raw_datasets
            ]
        topics.sort(key=lambda t: t["updated_at"] or "", reverse=True)
        return topics
    except Exception as e:
        print(f"[GetTopics] Failed: {e}")
        return []


async def reset_memory():
    global _learning_profile_cache
    _learning_profile_cache = None
    try:
        if COGNEE_MODE == "cloud":
            datasets = await asyncio.to_thread(cloud_list_datasets)
            for ds in datasets:
                await asyncio.to_thread(cloud_delete_dataset, ds["id"])
            return "🗑️ Cloud memory cleared!"

        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
        return "🗑️ Memory cleared!"
    except Exception as e:
        print(f"[ResetMemory] Failed: {e}")
        return f"❌ Could not clear memory: {e}"


# ─────────────────────────────────────────────
# NEW FEATURES
# ─────────────────────────────────────────────

def _coerce_int(val, default: int = 50, lo: int = 0, hi: int = 100) -> int:
    """Safely coerce a value to an int clamped to [lo, hi]."""
    try:
        return max(lo, min(hi, int(val)))
    except (TypeError, ValueError):
        return default


def _coerce_str_list(val, default=None) -> list:
    """Safely coerce a value to a list of non-empty strings."""
    if default is None:
        default = []
    if not isinstance(val, list):
        return default
    return [str(item).strip() for item in val if str(item).strip()]


async def get_knowledge_graph(dataset_name: str = "studymate") -> dict:
    """Extract concepts and relationships from notes to build an interactive knowledge graph."""
    dataset_name = sanitize_name(dataset_name)

    summary_text = await _get_summary_text(
        "List all key concepts, topics, terms, and how they relate to each other in detail.",
        dataset_name
    )

    if not summary_text.strip():
        return {"nodes": [], "edges": []}

    prompt = f"""From the following study notes, extract the key concepts and their relationships to build a knowledge graph.

Study material:
{summary_text}

Return ONLY valid JSON in this exact format, nothing else:
{{
  "nodes": ["Concept1", "Concept2", "Concept3"],
  "edges": [
    {{"from": "Concept1", "to": "Concept2", "label": "uses"}},
    {{"from": "Concept2", "to": "Concept3", "label": "contains"}}
  ]
}}

Rules:
- Extract 8–15 important concepts as nodes (short names, 1-3 words each)
- Create edges showing how concepts relate (use labels like: uses, causes, is part of, prevents, manages, requires, enables, types of)
- Ensure every node appears in at least one edge
- Do NOT include duplicate edges
"""

    raw = safe_ollama_chat(prompt)
    result = parse_json_response(raw)

    # Strict normalisation — never let malformed model output reach the UI
    if not isinstance(result, dict):
        return {"nodes": [], "edges": []}

    raw_nodes = result.get("nodes", [])
    nodes = _coerce_str_list(raw_nodes, [])

    raw_edges = result.get("edges", [])
    edges = []
    node_set = set(nodes)
    if isinstance(raw_edges, list):
        for e in raw_edges:
            if not isinstance(e, dict):
                continue
            src = str(e.get("from", "")).strip()
            dst = str(e.get("to", "")).strip()
            lbl = str(e.get("label", "relates to")).strip() or "relates to"
            if src and dst:
                edges.append({"from": src, "to": dst, "label": lbl})
                # Add any novel node the model put only in edges
                node_set.update([src, dst])

    return {"nodes": list(node_set), "edges": edges}


async def get_learning_dna(dataset_name: str = "studymate") -> dict:
    """Generate a Learning DNA profile from notes and quiz history."""
    dataset_name = sanitize_name(dataset_name)

    _DNA_FALLBACK = {
        "learning_styles": ["Examples", "Step-by-step"],
        "knowledge_pct": 50,
        "confidence_pct": 50,
        "revision_topics": ["Review your notes to generate profile"],
        "exam_readiness_pct": 50,
    }

    async def fetch_notes():
        return await _get_summary_text(
            "What topics has the student covered and what are the main subject areas?",
            dataset_name
        )

    async def fetch_struggles():
        try:
            if COGNEE_MODE == "cloud":
                results = await asyncio.to_thread(cloud_search, "What has the student struggled with?", "struggle_history")
            else:
                await setup_cognee()
                results = await cognee.search(
                    query_text="What has the student struggled with?",
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=["struggle_history"]
                )
            return extract_text(results)
        except Exception:
            return ""

    summary_text, struggle_text = await asyncio.gather(fetch_notes(), fetch_struggles())

    prompt = f"""Based on the following study data, create a detailed Learning DNA profile for this student.

Topics studied:
{summary_text or "No notes available yet."}

Weak areas and struggles:
{struggle_text or "No struggles recorded yet."}

Return ONLY valid JSON in this exact format:
{{
  "learning_styles": ["Analogies", "Examples", "Step-by-step"],
  "knowledge_pct": 75,
  "confidence_pct": 65,
  "revision_topics": ["Topic 1", "Topic 2", "Topic 3"],
  "exam_readiness_pct": 70
}}

Rules:
- learning_styles: list 2-4 styles that match this student (choose from: Analogies, Examples, Step-by-step, Visual, Practice Problems, Concept Maps, Summaries)
- knowledge_pct: 0-100 integer, how well they know the material based on notes coverage
- confidence_pct: 0-100 integer, estimated confidence based on struggles and quiz performance
- revision_topics: 2-4 topics most needing revision (from weak areas/struggles)
- exam_readiness_pct: 0-100 integer, overall exam readiness score
"""

    raw = safe_ollama_chat(prompt)
    result = parse_json_response(raw)
    if not isinstance(result, dict):
        return _DNA_FALLBACK

    # Normalise every field — never trust raw LLM output types
    return {
        "learning_styles": _coerce_str_list(
            result.get("learning_styles"), ["Examples", "Step-by-step"]
        ),
        "knowledge_pct": _coerce_int(result.get("knowledge_pct", 50)),
        "confidence_pct": _coerce_int(result.get("confidence_pct", 50)),
        "revision_topics": _coerce_str_list(
            result.get("revision_topics"), ["Review your notes to generate profile"]
        ),
        "exam_readiness_pct": _coerce_int(result.get("exam_readiness_pct", 50)),
    }


async def predict_exam(dataset_name: str = "studymate") -> dict:
    """Predict exam performance based on notes and quiz/struggle history."""
    dataset_name = sanitize_name(dataset_name)

    _EXAM_FALLBACK = {
        "expected_score_pct": 70,
        "confidence_pct": 75,
        "weak_topics": ["Review your weak areas", "Take more quizzes"],
        "estimated_revision_hours": 5,
        "most_important_topic": "Review all topics",
    }

    async def fetch_notes():
        return await _get_summary_text(
            "What topics has the student covered and how thoroughly?",
            dataset_name
        )

    async def fetch_struggles():
        try:
            if COGNEE_MODE == "cloud":
                results = await asyncio.to_thread(cloud_search, "What are the student's weak areas and mistakes?", "struggle_history")
            else:
                await setup_cognee()
                results = await cognee.search(
                    query_text="What are the student's weak areas and mistakes?",
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=["struggle_history"]
                )
            return extract_text(results)
        except Exception:
            return ""

    summary_text, struggle_text = await asyncio.gather(fetch_notes(), fetch_struggles())

    prompt = f"""Based on the following study data, predict this student's exam performance.

Topics studied:
{summary_text or "No notes available yet."}

Weak areas and struggles:
{struggle_text or "No struggles recorded yet."}

Return ONLY valid JSON in this exact format:
{{
  "expected_score_pct": 82,
  "confidence_pct": 88,
  "weak_topics": ["Topic 1", "Topic 2", "Topic 3"],
  "estimated_revision_hours": 5,
  "most_important_topic": "Topic 1"
}}

Rules:
- expected_score_pct: 0-100 integer, realistic predicted exam score
- confidence_pct: 0-100 integer, how confident you are in this prediction
- weak_topics: 2-4 topics most likely to cost marks in an exam
- estimated_revision_hours: positive integer, realistic total hours needed to shore up weak areas
- most_important_topic: the single most critical topic to focus on right now (string)
"""

    raw = safe_ollama_chat(prompt)
    result = parse_json_response(raw)
    if not isinstance(result, dict):
        return _EXAM_FALLBACK

    # Normalise every field — coerce types, clamp ranges, use fallbacks
    weak_topics = _coerce_str_list(
        result.get("weak_topics"), ["Review your weak areas", "Take more quizzes"]
    )
    most_important = str(result.get("most_important_topic", "Review all topics")).strip()
    if not most_important:
        most_important = weak_topics[0] if weak_topics else "Review all topics"

    try:
        rev_hours = max(1, int(result.get("estimated_revision_hours", 5)))
    except (TypeError, ValueError):
        rev_hours = 5

    return {
        "expected_score_pct": _coerce_int(result.get("expected_score_pct", 70)),
        "confidence_pct": _coerce_int(result.get("confidence_pct", 75)),
        "weak_topics": weak_topics,
        "estimated_revision_hours": rev_hours,
        "most_important_topic": most_important,
    }
