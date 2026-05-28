"""Module transversal — LLM Router (cascade par coût).

Charge `data/config/llm_routing.json` et expose une fonction `call_llm(task_id, prompt)`
qui essaie le provider primaire, puis enchaîne sur la fallback_chain en cas
d'échec (quota, erreur réseau, refus contenu).

Implémentation des appels providers déférée : ce squelette devient fonctionnel
dès que les variables d'environnement correspondantes sont définies. En attendant
(pas de clés API), il sert de point d'extension propre.

Aucun secret dans le code — tout passe par os.environ.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTING_PATH = REPO_ROOT / "data" / "config" / "llm_routing.json"
USAGE_DIR = REPO_ROOT / "data" / "runtime"

log = logging.getLogger(__name__)


class LLMRouterError(Exception):
    pass


class NoProviderAvailable(LLMRouterError):
    pass


class TaskNotConfigured(LLMRouterError):
    pass


@dataclass
class LLMResponse:
    provider: str
    model: str
    text: str
    tokens_used: int
    latency_ms: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


def _load_routing() -> dict:
    return json.loads(ROUTING_PATH.read_text(encoding="utf-8"))


def _record_usage(provider: str, tokens: int) -> None:
    """Module 27 — Comptable Quota : enregistre la consommation."""
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    month_key = time.strftime("%Y-%m")
    path = USAGE_DIR / f"llm_usage_{month_key}.json"
    data: dict[str, int] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data[provider] = data.get(provider, 0) + tokens
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _provider_credentials_present(provider: str) -> bool:
    env_keys = {
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "cohere": "COHERE_API_KEY",
        "huggingface": "HF_API_KEY",
        "replicate": "REPLICATE_API_TOKEN",
        "perplexity": "PERPLEXITY_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "local": "_local_no_key_needed",
    }
    key = env_keys.get(provider)
    if key == "_local_no_key_needed":
        return True
    return bool(key and os.environ.get(key))


def _call_gemini(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    # Implémentation déférée : importer google.generativeai et appeler.
    # Pour l'instant, on lève une erreur explicite si appelé sans la lib.
    raise NotImplementedError(
        "Gemini call non implémenté — branchez google-generativeai et GEMINI_API_KEY"
    )


def _call_groq(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError("Groq call non implémenté — branchez groq SDK et GROQ_API_KEY")


def _call_mistral(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError(
        "Mistral call non implémenté — branchez mistralai SDK et MISTRAL_API_KEY"
    )


def _call_cohere(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError("Cohere call non implémenté — branchez cohere SDK et COHERE_API_KEY")


def _call_huggingface(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError("HF call non implémenté — branchez huggingface_hub et HF_API_KEY")


def _call_perplexity(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError("Perplexity call non implémenté — REST API + PERPLEXITY_API_KEY")


def _call_openrouter(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError("OpenRouter call non implémenté — REST API + OPENROUTER_API_KEY")


def _call_claude(model: str, prompt: str, max_tokens: int) -> LLMResponse:
    raise NotImplementedError("Claude API call non implémenté — anthropic SDK + ANTHROPIC_API_KEY")


PROVIDER_DISPATCH = {
    "gemini": _call_gemini,
    "groq": _call_groq,
    "mistral": _call_mistral,
    "cohere": _call_cohere,
    "huggingface": _call_huggingface,
    "perplexity": _call_perplexity,
    "openrouter": _call_openrouter,
    "claude": _call_claude,
}


def call_llm(task_id: str, prompt: str, max_tokens: int | None = None) -> LLMResponse:
    """Appelle le LLM approprié pour `task_id` en suivant la cascade `llm_routing.json`.

    Lève NoProviderAvailable si tous les providers de la chaîne échouent ou
    n'ont pas leurs clés. Lève TaskNotConfigured si task_id absent du routing.
    """
    routing = _load_routing()
    task_config = routing["tasks"].get(task_id)
    if not task_config:
        raise TaskNotConfigured(f"Tâche '{task_id}' absente de llm_routing.json")

    chain = [task_config["primary"]] + list(task_config.get("fallback_chain", []))
    errors: list[str] = []

    for entry in chain:
        provider = entry["provider"]
        model = entry.get("model", "")
        max_tk = max_tokens or entry.get("max_tokens", 2000)

        if not _provider_credentials_present(provider):
            errors.append(f"{provider}: credentials absentes")
            continue

        dispatch = PROVIDER_DISPATCH.get(provider)
        if not dispatch:
            errors.append(f"{provider}: dispatch non implémenté")
            continue

        try:
            response = dispatch(model, prompt, max_tk)
            _record_usage(provider, response.tokens_used)
            return response
        except NotImplementedError as exc:
            errors.append(f"{provider}/{model}: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            log.warning("Provider %s/%s a échoué : %s", provider, model, exc)
            errors.append(f"{provider}/{model}: {type(exc).__name__}: {exc}")
            continue

    raise NoProviderAvailable(
        f"Aucun provider disponible pour task='{task_id}'. Erreurs : {errors}"
    )


def task_is_claude_reserved(task_id: str) -> bool:
    routing = _load_routing()
    task_config = routing["tasks"].get(task_id, {})
    return task_config.get("primary", {}).get("provider") == "claude"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m scripts.lib.llm_router <task_id>", file=sys.stderr)
        print("Liste des tâches disponibles :", file=sys.stderr)
        try:
            r = _load_routing()
            for tid in r["tasks"]:
                print(f"  - {tid}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            pass
        sys.exit(2)
    task = sys.argv[1]
    is_claude = task_is_claude_reserved(task)
    print(json.dumps({"task_id": task, "claude_reserved": is_claude}, indent=2))
