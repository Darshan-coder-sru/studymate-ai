import ollama
import cognee
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def setup_cognee():
    cognee.config.set_llm_config({
        "llm_provider": "ollama",
        "llm_model": "phi3",                          # ← removed "ollama/" prefix
        "llm_endpoint": "http://localhost:11434/v1",  # ← added /v1
        "llm_api_key": "ollama"
    })
    cognee.config.set_embedding_config({
        "embedding_provider": "ollama",
        "embedding_model": "nomic-embed-text",
        "embedding_endpoint": "http://localhost:11434/v1",  # ← added /v1
        "embedding_api_key": "ollama"
    })

async def add_notes(text: str, dataset_name: str = "studymate"):
    await setup_cognee()
    await cognee.add(text, dataset_name=dataset_name)
    # await cognee.cognify([dataset_name])
    return "✅ Notes added to memory!"

async def ask_question(question: str):
    await setup_cognee()
    # results = await cognee.search(question)
    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": question}]
    )
    return [response.message.content]

async def reset_memory():
    await cognee.prune.prune_data()
    return "🗑️ Memory cleared!"