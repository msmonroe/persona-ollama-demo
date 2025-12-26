# Persona Creator Demo (WoW-style) + Ollama 🦙

A local demo that lets you pick an AI "Class" + "Spec" (WoW-style), customize visual avatars, and generates a system prompt that steers a local Ollama model. Features real-time streaming responses for an interactive chat experience.

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
```

## Run
```bash
streamlit run app.py
```

## Test
```bash
pytest -q
```

## Notes
- Personas are presentation-layer instructions, not "entities".
- A Persona Badge is always shown to keep the experience grounded.
