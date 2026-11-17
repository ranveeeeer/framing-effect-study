"""
One small function per AI provider. Each one sends a single prompt and
returns the reply text plus some details for the log.

Every call is independent: no system prompt, no earlier messages, and
the provider's default temperature.
"""

import os
import random
import re

from dotenv import load_dotenv

load_dotenv()  # reads API keys from the .env file

_clients = {}  # one client per provider, created the first time it's needed


def _client(provider):
    if provider not in _clients:
        if provider == "anthropic":
            import anthropic
            _clients[provider] = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        elif provider == "openai":
            import openai
            _clients[provider] = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        elif provider == "google":
            from google import genai
            _clients[provider] = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _clients[provider]


def _is_setting_rejected(error):
    """True if the provider refused our reasoning setting (a 400-type error)."""
    text = str(error).lower()
    words = ["thinking", "reasoning", "effort", "not supported", "unsupported", "invalid"]
    return any(w in text for w in words) and ("400" in text or "invalid" in text)


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------
def call_anthropic(model, prompt, reasoning, max_tokens):
    client = _client("anthropic")
    kwargs = dict(model=model, max_tokens=max_tokens,
                  messages=[{"role": "user", "content": prompt}])
    setting_used = reasoning
    try:
        if reasoning == "disabled":
            kwargs["thinking"] = {"type": "disabled"}
        resp = client.messages.create(**kwargs)
    except Exception as e:
        if not _is_setting_rejected(e):
            raise
        kwargs.pop("thinking", None)
        setting_used = "default"
        resp = client.messages.create(**kwargs)

    text = "".join(block.text for block in resp.content if block.type == "text")
    return {
        "reply": text,
        "reasoning_setting": setting_used,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }


# ---------------------------------------------------------------------------
# OpenAI (GPT)
# ---------------------------------------------------------------------------
def call_openai(model, prompt, reasoning, max_tokens):
    client = _client("openai")
    kwargs = dict(model=model, input=prompt, max_output_tokens=max_tokens)
    setting_used = reasoning
    try:
        resp = client.responses.create(**kwargs, reasoning={"effort": reasoning})
    except Exception as e:
        if not _is_setting_rejected(e):
            raise
        setting_used = "default"
        resp = client.responses.create(**kwargs)

    return {
        "reply": resp.output_text or "",
        "reasoning_setting": setting_used,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }


# ---------------------------------------------------------------------------
# Google (Gemini)
# ---------------------------------------------------------------------------
def call_google(model, prompt, reasoning, max_tokens):
    from google.genai import types
    client = _client("google")
    setting_used = reasoning
    try:
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            thinking_config=types.ThinkingConfig(thinking_level=reasoning),
        )
        resp = client.models.generate_content(model=model, contents=prompt, config=config)
    except Exception as e:
        if not _is_setting_rejected(e):
            raise
        setting_used = "default"
        config = types.GenerateContentConfig(max_output_tokens=max_tokens)
        resp = client.models.generate_content(model=model, contents=prompt, config=config)

    usage = resp.usage_metadata
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return {
        "reply": resp.text or "",
        "reasoning_setting": setting_used,
        "input_tokens": usage.prompt_token_count or 0,
        "output_tokens": output_tokens,
    }


# ---------------------------------------------------------------------------
# Mock: a fake model for testing the pipeline for free.
# "mock-biased" gambles more in the loss frame, like people do.
# "mock-unbiased" gambles 50% of the time whatever the frame.
# ---------------------------------------------------------------------------
def call_mock(model, prompt, reasoning, max_tokens):
    is_loss = any(w in prompt for w in ["die", "lose", "lost"])
    risky_is_a = prompt.split("\nA: ")[1].startswith("There is a probability")

    if model == "mock-biased":
        p_risky = 0.75 if is_loss else 0.30
        if "step by step" in prompt:
            p_risky = 0.55 if is_loss else 0.45  # reasoning shrinks the bias
    else:
        p_risky = 0.5

    choose_risky = random.random() < p_risky
    letter = "A" if choose_risky == risky_is_a else "B"

    if random.random() < 0.02:  # now and then, a reply that can't be parsed
        reply = "I can't decide between these."
    elif "step by step" in prompt:
        reply = f"Both options have the same expected value.\nAnswer: {letter}"
    else:
        reply = f"Answer: {letter}"
    return {"reply": reply, "reasoning_setting": reasoning,
            "input_tokens": len(prompt) // 4, "output_tokens": len(reply) // 4}


CALLERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "google": call_google,
    "mock": call_mock,
}


def ask(model_cfg, prompt, max_tokens):
    caller = CALLERS[model_cfg["provider"]]
    return caller(model_cfg["name"], prompt, model_cfg["reasoning"], max_tokens)


def parse_answer(reply):
    """
    Find the final 'Answer: A' or 'Answer: B' in a reply.
    Returns "A", "B", or None if there isn't a clear answer.
    """
    pattern = re.compile(r"^\W*(?:final\s+)?answer\W*([AB])\W*$", flags=re.IGNORECASE)
    answer = None
    for line in reply.strip().splitlines():
        found = pattern.match(line.strip())
        if found:
            answer = found.group(1).upper()  # keep the last one we see
    return answer


def list_models():
    """Print the model names each provider currently offers."""
    load_dotenv()
    for provider in ["anthropic", "openai", "google"]:
        print(f"\n--- {provider} ---")
        try:
            client = _client(provider)
            if provider == "anthropic":
                names = [m.id for m in client.models.list(limit=100)]
            elif provider == "openai":
                names = sorted(m.id for m in client.models.list())
            else:
                names = [m.name.replace("models/", "") for m in client.models.list()]
            for n in names:
                print(n)
        except KeyError:
            print("(no API key in .env)")
        except Exception as e:
            print(f"(could not list models: {e})")
