import os

def read_scope_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "prompts", "scope", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
