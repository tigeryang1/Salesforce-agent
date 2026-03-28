from __future__ import annotations

import json
from typing import Any


def extract_text(result: Any) -> str:
    if isinstance(result, dict):
        msgs = result.get("messages")
        if msgs and isinstance(msgs, list):
            last = msgs[-1]
            content = getattr(last, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                chunks = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        chunks.append(item["text"])
                if chunks:
                    return "\n".join(chunks)
        output = result.get("output")
        if isinstance(output, str):
            return output
    if isinstance(result, str):
        return result
    return json.dumps(result, default=str)


def classify_intent(user_input: str) -> str:
    text = user_input.lower()
    write_words = {
        "update",
        "create",
        "optimize",
        "delete",
        "change",
        "adjust",
        "increase",
        "decrease",
        "close case",
    }
    return "write" if any(word in text for word in write_words) else "read"


def parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
