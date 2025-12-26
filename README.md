# Persona Creator Demo (WoW-style) + Multi-Model AI 🤖

A local demo that lets you pick an AI **Class** + **Spec** (WoW-style), customize visual avatars, and generates a **system prompt** that steers multiple AI models. Includes **real-time streaming**, plus **save/load** for custom personas. Supports **Ollama**, **OpenAI**, **Anthropic (Claude)**, **Google (Gemini)**, **xAI (Grok)**, and **DeepSeek**.

**Version 1.3** - Latest features include conversation management and enhanced theming.

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
- **Streaming responses** (real-time chat generation)
- **Avatar customization** (visual-only)
- **Save/Load** custom personas
- **Conversation Management**:
  - Save and load conversations
  - Conversation history with search and delete
  - Auto-generated conversation titles
  - Export conversations (JSON, Text, Markdown)
  - Persistent chat history across sessions
- **Multi-Model Support**: Ollama, OpenAI, Anthropic, Google, xAI, DeepSeek
- **Enhanced Theming**: Light/dark themes with WoW class-specific color schemes

## Prereqs

### For Ollama (Local Models)
- Ollama installed and running
- A model pulled, e.g.:
  - `ollama pull llama3.2` (recommended - smaller and faster)
  - `ollama pull mistral` (alternative)
- **Note:** Some large models may require significant RAM. The app prioritizes smaller, compatible models by default.

### For Cloud Models (Optional)
Copy `.env.example` to `.env` and add your API keys:
```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
XAI_API_KEY=your_xai_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env to add your API keys for cloud providers (optional)

## run
streamlit run app.py

## Test
pytest -q
## Conversation Management

The app includes comprehensive conversation management features:

### Saving Conversations
- Conversations are automatically saved when you start a new chat or close the app
- You can manually save conversations with custom titles
- Conversations include metadata (persona, model, timestamps)

### Loading Conversations
- Browse your conversation history in the expandable "Conversation History" section
- Load any previous conversation to continue chatting
- Conversations are sorted by most recent activity

### Exporting Conversations
- Export conversations in multiple formats:
  - **JSON**: Full conversation data for backup/import
  - **Text**: Human-readable format with timestamps
  - **Markdown**: Formatted for documentation or sharing

### Managing Conversations
- Delete unwanted conversations from your history
- Conversations are stored locally in the `saved_conversations/` directory
- Each conversation has a unique ID and maintains full message history
## Troubleshooting

### Ollama 500 Internal Server Error
If you get a "500 Server Error" when chatting with Ollama:
- **Cause:** Large models may require more RAM than available on your system
- **Solution:** The app automatically prioritizes smaller models (llama3.2:latest, llama3.2:3b, etc.)
- **Manual fix:** Pull a smaller model with `ollama pull llama3.2` and restart the app

### Model Not Found
- Ensure Ollama is running: `ollama serve`
- Pull the desired model: `ollama pull <model_name>`
- Check available models: `ollama list`

### Slow Responses
- Try smaller models like `llama3.2:3b` instead of larger ones
- Close other memory-intensive applications
- Consider using cloud providers for faster inference

## Personas are presentation-layer instructions, not "entities".

## The Persona Badge is always shown to keep the experience grounded.


## If you want one extra “nice touch” for credibility: add a tiny **“About this chat”** section in the UI (or README) that lists model name + persona settings. It reinforces “this is a configuration,” and it makes screenshots self-explanatory.
## ::contentReference[oaicite:0]{index=0}

