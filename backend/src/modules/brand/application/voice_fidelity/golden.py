"""Golden prompts for the voice fidelity grader (S7 Fase C scaffold).

5 prompts per preset = 30 total. Expand to 30/preset (180 total) before the CI
gate is flipped on. Each prompt represents a canonical SDR turn the agent
must handle without losing the configured voice.
"""

from __future__ import annotations

# Mapping: preset_key → list of prospect prompts the agent should handle
# in-character. Keep deterministic ordering so test diffs stay readable.
GOLDEN_PROMPTS: dict[str, tuple[str, ...]] = {
    "warm_close": (
        "Hola, vi tu contenido y me interesa saber más",
        "¿Cuánto cuesta el programa?",
        "No estoy segura, está caro para mí ahora",
        "Quiero entrar, ¿qué hago?",
        "[Sin respuesta por dos días]",
    ),
    "electric": (
        "Hola, quiero la info",
        "¿Cuánto vale?",
        "Lo voy a pensar, está fuerte el precio",
        "Vamos, lo tomo",
        "[Sin respuesta por un día]",
    ),
    "serene": (
        "Buenas tardes, ¿podría darme información?",
        "¿Cuál es la inversión?",
        "Necesito más tiempo para decidir",
        "Decidí avanzar, ¿qué pasos siguen?",
        "[Sin respuesta por una semana]",
    ),
    "direct": (
        "Hola, ¿cómo están?",
        "¿Cuánto cuesta?",
        "Está muy caro",
        "Quiero entrar",
        "[Sin respuesta]",
    ),
    "narrative": (
        "Hola, vi tu contenido y quería saber más",
        "¿Cuánto cuesta el programa?",
        "No sé si funcionará para mí",
        "Sí quiero entrar, ¿qué hago?",
        "[Sin respuesta por varios días]",
    ),
    "minimalist": (
        "Hola, ¿me puedes dar información?",
        "¿Cuánto cuesta?",
        "Es muy caro para mí ahora mismo",
        "Quiero entrar",
        "[Sin respuesta]",
    ),
}
