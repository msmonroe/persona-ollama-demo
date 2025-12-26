# Persona Creator Demo (WoW-style) + Ollama 🦙

A local demo that lets you pick an AI **Class** + **Spec** (WoW-style), customize visual avatars, and generates a **system prompt** that steers a local Ollama model. Includes **real-time streaming**, plus **save/load** for custom personas.

## Why this exists (product rationale)

Chatbots often feel inconsistent because multiple factors change independently (model variants, tool access, tuning, context). This demo makes behavior **explicit and user-controlled** by turning “vibes” into **knobs**:

- **Predictability:** Users choose the interaction style they want (e.g., *Rogue/Speed* vs *Paladin/Accuracy*).
- **Shared language:** “Use Mage/Teacher” is clearer than “be helpful but not too verbose.”
- **Reproducibility:** Support/debug is easier when behavior is tied to a visible configuration.

## Safety framing

Personas here are **presentation-layer interaction presets**, not characters with agency. The UI keeps this grounded with an always-visible **Persona Badge** (Class/Spec/Mode), and the generated system prompt includes guardrails to avoid “entity” framing.

Design goal: **increase user satisfaction and usability while reducing risk** via clarity, consistency, and a visible “mode” contract.

## Features

- **WoW-style Class/Spec** persona builder
- **Persona Badge** always visible (Class/Spec/Mode)
- **Streaming responses** (Ollama `/api/chat` streaming)
- **Avatar customization** (visual-only)
- **Save/Load** custom personas

## Prereqs

- Ollama installed and running
- A model pulled, e.g.:
  - `ollama pull llama3.2`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env

## run
streamlit run app.py

## Test
pytest -q

## Notes

## Personas are presentation-layer instructions, not "entities".

## The Persona Badge is always shown to keep the experience grounded.


## If you want one extra “nice touch” for credibility: add a tiny **“About this chat”** section in the UI (or README) that lists model name + persona settings. It reinforces “this is a configuration,” and it makes screenshots self-explanatory.
## ::contentReference[oaicite:0]{index=0}

