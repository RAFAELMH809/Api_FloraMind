import asyncio
from app.core.config import MAX_CONCURRENT_PREDICTIONS

semaphore = asyncio.Semaphore(MAX_CONCURRENT_PREDICTIONS)
