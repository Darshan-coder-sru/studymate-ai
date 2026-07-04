import os
import cognee

async def use_cloud_memory():
    """Connect to Cognee Cloud using credentials from .env"""
    await cognee.serve(
        url=os.environ["https://tenant-5f979234-c03d-46c6-aa38-ff939b38b480.aws.cognee.ai"],
        api_key=os.environ["032fafd77b4a359a83fe2798d289ff97d46bf8d96675cd1f79e9c926aa85c0ce"]
    )

async def remember(text: str):
    await cognee.remember(text)

async def recall(query: str):
    return await cognee.recall(query)

async def disconnect_cloud():
    await cognee.disconnect()