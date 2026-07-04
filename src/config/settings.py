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

# Prevent LangChain from printing annoying warnings if both keys are in the system environment
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

# Model configuration
MODEL_NAME = "gemini-2.5-flash"

class RequestCounter:
    def __init__(self):
        self.count = 0
        self._lock = None

    @property
    def lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def check_and_wait(self):
        async with self.lock:
            self.count += 1
            if self.count >= 10:
                print("\n[Strict Limiter] Reached 10 requests. Sleeping for 60 seconds...")
                await asyncio.sleep(60)
                self.count = 0

global_counter = RequestCounter()

class ThrottledGemini(ChatGoogleGenerativeAI):
    """Subclass to catch 429 errors and sleep without crashing."""
    async def _agenerate(self, *args, **kwargs):
        # Optional strict counter
        await global_counter.check_and_wait()
        
        max_retries = 10
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
                    print(f"\n[Rate Limiter] Google blocked request. Sleeping {wait_time:.1f}s to recover...")
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
