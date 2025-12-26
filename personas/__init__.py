"""Personas module - WoW-style persona configuration and prompt building."""

from .presets import PRESETS, CLASS_FLAVOR, SPEC_BEHAVIOR, PersonaPreset
from .prompt_builder import PersonaConfig, build_system_prompt

__all__ = [
    "PRESETS",
    "CLASS_FLAVOR",
    "SPEC_BEHAVIOR",
    "PersonaPreset",
    "PersonaConfig",
    "build_system_prompt",
]
