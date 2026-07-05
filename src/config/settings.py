"""
Configuration settings for the Multi-Agent Orchestration project.
Loads environment variables and provides the configured LLM instance.
"""

import os
import asyncio
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Suppress the LangChain annoying warning by removing the redundant key from the runtime
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

# Model configuration
MODEL_NAME = "gemini-3.1-flash-lite"


class SlidingWindowRateLimiter:
    """
    Tracks request timestamps in a sliding 60-second window.
    Strictly limits to 10 Requests Per Minute (RPM) as requested.
    """
    def __init__(self, rpm: int = 14, window: int = 60):
        self.rpm = rpm
        self.window = window
        self.timestamps: list[float] = []
        self._lock = None

    @property
    def lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def _purge_old(self):
        """Remove timestamps older than 60 seconds."""
        cutoff = time.time() - self.window
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    async def acquire(self):
        """Async path — waits until a slot is available."""
        async with self.lock:
            self._purge_old()
            if len(self.timestamps) >= self.rpm:
                oldest = self.timestamps[0]
                sleep_for = (oldest + self.window) - time.time() + 0.5
                if sleep_for > 0:
                    print(f"\nAgent is sleeping...")
                    await asyncio.sleep(sleep_for)
                    self._purge_old()
            self.timestamps.append(time.time())

    def acquire_sync(self):
        """Sync path — waits until a slot is available."""
        self._purge_old()
        if len(self.timestamps) >= self.rpm:
            oldest = self.timestamps[0]
            sleep_for = (oldest + self.window) - time.time() + 0.5
            if sleep_for > 0:
                print(f"\nAgent is sleeping...")
                time.sleep(sleep_for)
                self._purge_old()
        self.timestamps.append(time.time())

rate_limiter = SlidingWindowRateLimiter(rpm=10, window=60)

class ThrottledGemini(ChatGoogleGenerativeAI):
    """Wraps every Gemini call with sliding-window RPM limiting and 429 retry logic."""
    def _generate(self, *args, **kwargs):
        rate_limiter.acquire_sync()
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return super()._generate(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt == max_retries - 1:
                        raise e
                    import re
                    match = re.search(r"retry in ([\d\.]+)s", error_msg)
                    wait_time = float(match.group(1)) + 2.0 if match else 60.0
                    print(f"\n[429 Recovery] Google blocked request. Sleeping {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise e

    async def _agenerate(self, *args, **kwargs):
        await rate_limiter.acquire()
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return await super()._agenerate(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt == max_retries - 1:
                        raise e
                    import re
                    match = re.search(r"retry in ([\d\.]+)s", error_msg)
                    wait_time = float(match.group(1)) + 2.0 if match else 60.0
                    print(f"\n[429 Recovery] Google blocked request. Sleeping {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e


def get_llm(temperature: float = 0.0):
    """
    Creates and returns a configured Google Gemini LLM instance.

    Args:
        temperature: Controls randomness. 0.0 = deterministic, 1.0 = creative.

    Returns:
        A ChatGoogleGenerativeAI instance ready for use.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set in the environment.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Please add it to your .env file: GOOGLE_API_KEY=your-key-here"
        )

    return ThrottledGemini(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=temperature,
    )
