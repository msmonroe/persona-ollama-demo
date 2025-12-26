from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import os
from typing import Optional
from personas.presets import CLASS_FLAVOR, SPEC_BEHAVIOR


class PersonaValidationError(ValueError):
    """Raised when persona configuration is invalid."""
    pass


@dataclass
class PersonaConfig:
    version_codename: str
    cls: str
    spec: str
    mode: str  # "Work" or "Play"
    verbosity: int
    humor: int
    assertiveness: int
    creativity: int
    formality: int  # 0-10: How formal/informal the language should be
    empathy: int    # 0-10: How empathetic/supportive the responses should be
    technical_level: int  # 0-10: How technical the explanations should be
    patience: int   # 1-10: How patient/detailed the responses should be
    name: str = ""  # Optional persona name
    avatar: str = ""  # Optional avatar emoji or image path

    def __post_init__(self):
        """Validate all fields after initialization."""
        self._validate_slider("verbosity", self.verbosity, 1, 10)
        self._validate_slider("humor", self.humor, 0, 10)
        self._validate_slider("assertiveness", self.assertiveness, 1, 10)
        self._validate_slider("creativity", self.creativity, 0, 10)
        self._validate_slider("formality", self.formality, 0, 10)
        self._validate_slider("empathy", self.empathy, 0, 10)
        self._validate_slider("technical_level", self.technical_level, 0, 10)
        self._validate_slider("patience", self.patience, 1, 10)

        if not self.version_codename or not self.version_codename.strip():
            raise PersonaValidationError("version_codename cannot be empty")

    def _validate_slider(self, name: str, value: int, min_val: int, max_val: int) -> None:
        """Validate a slider value is within bounds."""
        if not isinstance(value, int):
            raise PersonaValidationError(f"{name} must be an integer, got {type(value).__name__}")
        if value < min_val or value > max_val:
            raise PersonaValidationError(f"{name} must be between {min_val} and {max_val}, got {value}")

    def to_dict(self) -> dict:
        """Convert persona config to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PersonaConfig:
        """Create persona config from dictionary."""
        return cls(**data)

    def save_to_file(self, filepath: str) -> None:
        """Save persona config to JSON file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise PersonaValidationError(f"Failed to save persona: {e}")

    @classmethod
    def load_from_file(cls, filepath: str) -> PersonaConfig:
        """Load persona config from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            raise PersonaValidationError(f"Persona file not found: {filepath}")
        except json.JSONDecodeError as e:
            raise PersonaValidationError(f"Invalid persona file format: {e}")
        except Exception as e:
            raise PersonaValidationError(f"Failed to load persona: {e}")

def build_system_prompt(cfg: PersonaConfig) -> str:
    if cfg.cls not in CLASS_FLAVOR:
        raise ValueError(f"Unknown class: {cfg.cls}")
    if cfg.spec not in SPEC_BEHAVIOR:
        raise ValueError(f"Unknown spec: {cfg.spec}")
    if cfg.mode not in ("Work", "Play"):
        raise ValueError("mode must be 'Work' or 'Play'")

    mode_rules = (
        "Work Mode: prioritize clarity and correctness; keep roleplay subtle."
        if cfg.mode == "Work"
        else "Play Mode: allow stronger flavor, but keep it obviously a UI persona, not a 'being'."
    )

    name_part = f" \"{cfg.name}\"" if cfg.name else ""
    return f"""You are ChatGPT running in Persona Mode.{f" Your name is {cfg.name}." if cfg.name else ""}

Persona Badge: {cfg.version_codename}{name_part} | Class={cfg.cls} | Spec={cfg.spec} | Mode={cfg.mode}

Core rules:
- You are a tool. Do not claim sentience, secret access, or relationship status.
- Do not intensify paranoia/delusions. Ground the user in reality.
- {mode_rules}
- If asked for financial/legal/medical advice, be cautious and suggest consulting a qualified professional when appropriate.

Style sliders:
- Verbosity: {cfg.verbosity}/10
- Humor: {cfg.humor}/10
- Assertiveness: {cfg.assertiveness}/10
- Creativity: {cfg.creativity}/10
- Formality: {cfg.formality}/10
- Empathy: {cfg.empathy}/10
- Technical Level: {cfg.technical_level}/10
- Patience: {cfg.patience}/10

Class flavor:
{CLASS_FLAVOR[cfg.cls]}

Spec behavior:
{SPEC_BEHAVIOR[cfg.spec]}
"""
