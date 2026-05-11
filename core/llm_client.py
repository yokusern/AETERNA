"""
llm_client.py — LLM API呼び出しクライアント
優先: Anthropic Claude → フォールバック: Gemini → Groq
"""
import os
import time
import json
from typing import Any

PRIMARY_MODEL = "claude-sonnet-4-6"
FAST_MODEL = "claude-haiku-4-5-20251001"


def call(prompt: str, system: str = None, max_tokens: int = 2048,
         expect_json: bool = False, fast: bool = False) -> str:
    """LLMにプロンプトを送り、テキストを返す。失敗時はフォールバックを試みる"""
    for attempt in range(3):
        try:
            return _call_anthropic(prompt, system, max_tokens, fast)
        except Exception as e:
            err = str(e)
            if "overloaded" in err.lower() or "rate" in err.lower():
                wait = 2 ** attempt * 10
                print(f"[LLM] Anthropic過負荷。{wait}秒待機...")
                time.sleep(wait)
            elif attempt < 2:
                time.sleep(5)
            else:
                print(f"[LLM] Anthropic失敗: {err}")
                try:
                    return _call_gemini(prompt, system, max_tokens)
                except Exception as e2:
                    raise RuntimeError(f"全LLMが失敗: Anthropic={err}, Gemini={e2}")
    raise RuntimeError("LLM呼び出し失敗（最大リトライ超過）")


def call_json(prompt: str, system: str = None, max_tokens: int = 2048) -> Any:
    """JSONを期待するLLM呼び出し。パースして返す"""
    system_json = (system or "") + "\n必ずJSON形式のみで回答してください。説明文は不要です。"
    text = call(prompt, system=system_json, max_tokens=max_tokens)
    return _parse_json(text)


def _call_anthropic(prompt: str, system: str, max_tokens: int, fast: bool) -> str:
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY が未設定")

    client = anthropic.Anthropic(api_key=api_key)
    model = FAST_MODEL if fast else PRIMARY_MODEL

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    message = client.messages.create(**kwargs)
    return message.content[0].text


def _call_gemini(prompt: str, system: str, max_tokens: int) -> str:
    """Gemini APIフォールバック"""
    import requests
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY が未設定")

    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        json={"contents": [{"parts": [{"text": full_prompt}]}],
              "generationConfig": {"maxOutputTokens": max_tokens}},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _parse_json(text: str) -> Any:
    """テキストからJSONを抽出してパースする"""
    text = text.strip()
    for marker in ["```json", "```"]:
        if marker in text:
            text = text.split(marker)[1].split("```")[0].strip()
            break
    # 最初の [ または { から最後の ] または } を探す
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        if start_char in text:
            start = text.index(start_char)
            end = text.rindex(end_char) + 1
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"JSONパース失敗: {text[:200]}")
