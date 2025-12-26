from __future__ import annotations
import os
from dotenv import load_dotenv
import streamlit as st

from ollama.client import chat as ollama_chat, chat_stream, health_check, OllamaConnectionError
from personas.presets import PRESETS, CLASS_FLAVOR, SPEC_BEHAVIOR, CLASS_AVATAR
from personas.prompt_builder import PersonaConfig, build_system_prompt

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
DEFAULT_VERSION = os.getenv("APP_VERSION", "ChatGPT 26.2: Redwood")

st.set_page_config(page_title="Persona Creator + Ollama", layout="wide")
st.title("Persona Creator Demo (WoW-style) + Ollama 🦙")

# Check Ollama connection on startup
@st.cache_data(ttl=30)
def check_ollama_status():
    """Check if Ollama is running (cached for 30 seconds)."""
    try:
        health_check()
        return True, None
    except OllamaConnectionError as e:
        return False, str(e)

ollama_healthy, ollama_error = check_ollama_status()
if not ollama_healthy:
    st.error(f"⚠️ Ollama not available: {ollama_error}")
    st.info("Make sure Ollama is running: `ollama serve`")

left, right = st.columns([1, 2])

def init_state():
    if "msgs" not in st.session_state:
        st.session_state.msgs = []
    if "selected_preset" not in st.session_state:
        st.session_state.selected_preset = PRESETS[0].key

init_state()

with left:
    st.subheader("Character Creator")

    preset_titles = {p.key: p.title for p in PRESETS}
    selected_preset_key = st.selectbox(
        "Preset",
        options=[p.key for p in PRESETS],
        format_func=lambda k: preset_titles[k],
        index=[p.key for p in PRESETS].index(st.session_state.selected_preset),
    )
    st.session_state.selected_preset = selected_preset_key
    preset = next(p for p in PRESETS if p.key == selected_preset_key)

    version_codename = st.text_input("Version + Codename", DEFAULT_VERSION)
    persona_name = st.text_input("Persona Name (optional)", preset.name, placeholder="e.g., Archmage Lyra")
    model = st.text_input("Ollama model", DEFAULT_MODEL)
    streaming_enabled = st.checkbox("Enable streaming responses", value=False, help="Show responses as they are generated in real-time")

    cls = st.selectbox("Class", list(CLASS_FLAVOR.keys()), index=list(CLASS_FLAVOR.keys()).index(preset.cls))
    default_avatar = CLASS_AVATAR.get(cls, "🧙‍♂️")
    avatar = st.selectbox("Avatar", list(CLASS_AVATAR.values()), index=list(CLASS_AVATAR.values()).index(default_avatar), format_func=lambda x: f"{x} {list(CLASS_AVATAR.keys())[list(CLASS_AVATAR.values()).index(x)]}")
    spec = st.selectbox("Spec", list(SPEC_BEHAVIOR.keys()), index=list(SPEC_BEHAVIOR.keys()).index(preset.spec))
    mode = st.radio("Mode", ["Work", "Play"], index=0 if preset.mode == "Work" else 1, horizontal=True)

    verbosity = st.slider("Verbosity", 1, 10, preset.verbosity)
    humor = st.slider("Humor", 0, 10, preset.humor)
    assertiveness = st.slider("Assertiveness", 1, 10, preset.assertiveness)
    creativity = st.slider("Creativity", 0, 10, preset.creativity)

    cfg = PersonaConfig(
        version_codename=version_codename,
        cls=cls,
        spec=spec,
        mode=mode,
        verbosity=verbosity,
        humor=humor,
        assertiveness=assertiveness,
        creativity=creativity,
        name=persona_name,
        avatar=avatar,
    )
    system_prompt = build_system_prompt(cfg)

    st.markdown("### Persona Badge")
    name_display = f" \"{persona_name}\"" if persona_name else ""
    st.markdown(f"{avatar} **{version_codename}{name_display}** | {cls} / {spec} | {mode}")
    st.code(f"{version_codename}{name_display} | {cls} / {spec} | {mode}")

    with st.expander("Generated system prompt"):
        st.code(system_prompt)

    if st.button("New Chat"):
        st.session_state.msgs = []
        st.rerun()

with right:
    st.subheader("Chat")

    for m in st.session_state.msgs:
        if m["role"] == "assistant":
            st.chat_message(m["role"], avatar=avatar).write(m["content"])
        else:
            st.chat_message(m["role"], avatar="👤").write(m["content"])

    user_text = st.chat_input("Ask something (try an accounting question)…")
    if user_text:
        st.session_state.msgs.append({"role": "user", "content": user_text})
        st.chat_message("user", avatar="👤").write(user_text)

        try:
            if streaming_enabled:
                # Streaming response
                with st.chat_message("assistant", avatar=avatar):
                    message_placeholder = st.empty()
                    accumulated_content = ""
                    
                    try:
                        for chunk in chat_stream(model=model, system_prompt=system_prompt, messages=st.session_state.msgs):
                            accumulated_content += chunk
                            message_placeholder.write(accumulated_content)
                    except Exception as e:
                        accumulated_content = f"Error during streaming: {e}"
                        message_placeholder.write(accumulated_content)
                    
                    reply = accumulated_content
            else:
                # Non-streaming response
                reply = ollama_chat(model=model, system_prompt=system_prompt, messages=st.session_state.msgs)
                st.chat_message("assistant", avatar=avatar).write(reply)
        except Exception as e:
            reply = f"Error talking to Ollama: {e}"
            st.chat_message("assistant", avatar=avatar).write(reply)

        st.session_state.msgs.append({"role": "assistant", "content": reply})
