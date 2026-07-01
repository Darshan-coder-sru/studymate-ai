import os
import re

# Set config BEFORE importing cognee
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
from cognee.api.v1.search import SearchType
import asyncio
from dotenv import load_dotenv

load_dotenv()

_learning_profile_cache = None


def sanitize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())


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
    dataset_name = sanitize_name(dataset_name)
    await setup_cognee()
    await cognee.add(text, dataset_name=dataset_name)
    await cognee.cognify([dataset_name])
    return "✅ Notes added and indexed into memory!"


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

    def extract_text(results):
        parts = []
        for r in results:
            if isinstance(r, dict) and "search_result" in r:
                parts.append(" ".join(r["search_result"]))
            else:
                parts.append(str(r))
        return "\n".join(parts)

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

    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.message.content
    except Exception as e:
        answer = (
            f"Could not generate an answer right now.\n"
            f"Error: {e}\n\n"
            f"Here is the raw context from your notes:\n{topic_context or 'None found.'}"
        )

    return [{"search_result": [answer]}]


async def save_struggle(dataset_name: str, question: str, correct_answer: str, user_answer: str):
    dataset_name = sanitize_name(dataset_name)
    await setup_cognee()
    struggle_note = (
        f"The student answered '{user_answer}' but the correct answer was '{correct_answer}' "
        f"for the question: '{question}'. This is a weak area that needs more revision."
    )
    await cognee.add(struggle_note, dataset_name="struggle_history")
    return struggle_note


async def get_weak_areas():
    await setup_cognee()
    try:
        results = await cognee.search(
            query_text="What topics and questions has the student struggled with or answered incorrectly?",
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
        return []


async def generate_quiz(dataset_name: str = "studymate", num_questions: int = 5):
    dataset_name = sanitize_name(dataset_name)
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
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


async def generate_flashcards(dataset_name: str = "studymate", num_cards: int = 5):
    dataset_name = sanitize_name(dataset_name)
    await setup_cognee()

    summary_results = await cognee.search(
        query_text="Summarize all the key concepts, terms, and definitions in these notes.",
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

    prompt = f"""Based on the following study material, create {num_cards} flashcards.
Each flashcard should have a short question or term on the front, and a clear answer or definition on the back.

Study material:
{summary_text}

Return ONLY valid JSON in this exact format, nothing else:
[
  {{
    "front": "What is ...",
    "back": "It is ..."
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
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


async def generate_study_plan(dataset_name: str = "studymate", days: int = 7):
    dataset_name = sanitize_name(dataset_name)
    await setup_cognee()

    async def fetch_notes_summary():
        try:
            results = await cognee.search(
                query_text="Summarize all key concepts and topics in these notes.",
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=[dataset_name]
            )
            return results
        except Exception:
            return []

    async def fetch_struggles():
        try:
            results = await cognee.search(
                query_text="What has the student struggled with?",
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=["struggle_history"]
            )
            return results
        except Exception:
            return []

    notes_results, struggle_results = await asyncio.gather(
        fetch_notes_summary(),
        fetch_struggles()
    )

    def extract_text(results):
        parts = []
        for r in results:
            if isinstance(r, dict) and "search_result" in r:
                parts.append(" ".join(r["search_result"]))
            else:
                parts.append(str(r))
        return "\n".join(parts)

    notes_text = extract_text(notes_results)
    struggle_text = extract_text(struggle_results)

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
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


async def delete_topic(dataset_name: str):
    """Delete a specific topic/dataset from Cognee memory."""
    dataset_name = sanitize_name(dataset_name)
    await setup_cognee()
    try:
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
        return []


async def reset_memory():
    global _learning_profile_cache
    _learning_profile_cache = None
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    return "🗑️ Memory cleared!"