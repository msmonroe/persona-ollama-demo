from __future__ import annotations
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st

from ollama.client import chat as ollama_chat, chat_stream, health_check, OllamaConnectionError
from models import registry
from personas.presets import PRESETS, CLASS_FLAVOR, SPEC_BEHAVIOR, CLASS_AVATAR
from personas.prompt_builder import PersonaConfig, build_system_prompt, PersonaValidationError, PersonaValidationError

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
DEFAULT_VERSION = os.getenv("APP_VERSION", "ChatGPT 26.2: Redwood")

st.set_page_config(page_title="Persona Creator + Multi-Model AI", layout="wide")
st.title("Persona Creator Demo (WoW-style) + Multi-Model AI 🤖")

# Check provider connection on startup
@st.cache_data(ttl=30)
def check_provider_status(provider_name: str):
    """Check if the selected provider is accessible (cached for 30 seconds)."""
    try:
        provider = registry.get_provider(provider_name)
        if provider and provider.health_check():
            return True, None
        else:
            return False, f"Cannot connect to {provider_name}"
    except Exception as e:
        return False, str(e)

# Provider health check will be done after provider selection
provider_healthy = True
provider_error = None

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
    
    # Check if we have a loaded custom persona
    if "loaded_config" in st.session_state:
        loaded_cfg = st.session_state.loaded_config
        # Use loaded config as defaults
        default_preset_key = "custom_loaded"
        default_version = loaded_cfg.version_codename
        default_name = loaded_cfg.name
        default_cls = loaded_cfg.cls
        default_spec = loaded_cfg.spec
        default_mode = loaded_cfg.mode
        default_verbosity = loaded_cfg.verbosity
        default_humor = loaded_cfg.humor
        default_assertiveness = loaded_cfg.assertiveness
        default_creativity = loaded_cfg.creativity
        default_avatar = loaded_cfg.avatar
    else:
        # Use preset defaults
        preset = next(p for p in PRESETS if p.key == st.session_state.selected_preset)
        default_preset_key = st.session_state.selected_preset
        default_version = DEFAULT_VERSION
        default_name = preset.name
        default_cls = preset.cls
        default_spec = preset.spec
        default_mode = preset.mode
        default_verbosity = preset.verbosity
        default_humor = preset.humor
        default_assertiveness = preset.assertiveness
        default_creativity = preset.creativity
        default_avatar = CLASS_AVATAR.get(preset.cls, "🧙‍♂️")
    
    selected_preset_key = st.selectbox(
        "Preset",
        options=[p.key for p in PRESETS],
        format_func=lambda k: preset_titles[k],
        index=[p.key for p in PRESETS].index(default_preset_key) if default_preset_key in [p.key for p in PRESETS] else 0,
    )
    
    # Clear loaded config if user selects a different preset
    if selected_preset_key != st.session_state.selected_preset and "loaded_config" in st.session_state:
        del st.session_state.loaded_config
    
    st.session_state.selected_preset = selected_preset_key
    
    # Only update defaults if not using loaded config
    if "loaded_config" not in st.session_state:
        preset = next(p for p in PRESETS if p.key == selected_preset_key)
        default_name = preset.name
        default_cls = preset.cls
        default_spec = preset.spec
        default_mode = preset.mode
        default_verbosity = preset.verbosity
        default_humor = preset.humor
        default_assertiveness = preset.assertiveness
        default_creativity = preset.creativity
        default_avatar = CLASS_AVATAR.get(preset.cls, "🧙‍♂️")

    version_codename = st.text_input("Version + Codename", default_version)
    persona_name = st.text_input("Persona Name (optional)", default_name, placeholder="e.g., Archmage Lyra")

    # Model Provider Selection
    available_providers = registry.get_available_providers()
    selected_provider_name = st.selectbox(
        "AI Model Provider",
        options=available_providers,
        index=available_providers.index("Ollama") if "Ollama" in available_providers else 0,
        help="Choose your AI model provider"
    )

    selected_provider = registry.get_provider(selected_provider_name)
    available_models = selected_provider.available_models if selected_provider else []

    selected_model = st.selectbox(
        f"{selected_provider_name} Model",
        options=available_models,
        index=0,
        help=f"Available models from {selected_provider_name}"
    )

    # API Key configuration for non-Ollama providers
    if selected_provider_name != "Ollama":
        api_key_env_var = f"{selected_provider_name.upper()}_API_KEY"
        current_key = os.getenv(api_key_env_var, "")
        api_key = st.text_input(
            f"{selected_provider_name} API Key",
            value=current_key,
            type="password",
            help=f"Enter your {selected_provider_name} API key"
        )
        if api_key and api_key != current_key:
            os.environ[api_key_env_var] = api_key
            # Reinitialize provider with new key
            if selected_provider_name == "OpenAI":
                from models.openai_provider import OpenAIProvider
                registry.register(OpenAIProvider(api_key))
            elif selected_provider_name == "Anthropic":
                from models.anthropic_provider import AnthropicProvider
                registry.register(AnthropicProvider(api_key))
            elif selected_provider_name == "Google":
                from models.google_provider import GoogleProvider
                registry.register(GoogleProvider(api_key))
            elif selected_provider_name == "xAI":
                from models.xai_provider import xAIProvider
                registry.register(xAIProvider(api_key))
            elif selected_provider_name == "DeepSeek":
                from models.deepseek_provider import DeepSeekProvider
                registry.register(DeepSeekProvider(api_key))

    streaming_enabled = st.checkbox("Enable streaming responses", value=False, help="Show responses as they are generated in real-time")

    # Check provider health
    provider_healthy, provider_error = check_provider_status(selected_provider_name)
    if not provider_healthy:
        st.error(f"⚠️ {selected_provider_name} not available: {provider_error}")
        if selected_provider_name == "Ollama":
            st.info("Make sure Ollama is running: `ollama serve`")
        else:
            st.info(f"Make sure your {selected_provider_name} API key is configured")

    cls = st.selectbox("Class", list(CLASS_FLAVOR.keys()), index=list(CLASS_FLAVOR.keys()).index(default_cls))
    default_avatar = CLASS_AVATAR.get(cls, "🧙‍♂️")
    avatar = st.selectbox("Avatar", list(CLASS_AVATAR.values()), index=list(CLASS_AVATAR.values()).index(default_avatar), format_func=lambda x: f"{x} {list(CLASS_AVATAR.keys())[list(CLASS_AVATAR.values()).index(x)]}")
    spec = st.selectbox("Spec", list(SPEC_BEHAVIOR.keys()), index=list(SPEC_BEHAVIOR.keys()).index(default_spec))
    mode = st.radio("Mode", ["Work", "Play"], index=0 if default_mode == "Work" else 1, horizontal=True)

    verbosity = st.slider("Verbosity", 1, 10, default_verbosity)
    humor = st.slider("Humor", 0, 10, default_humor)
    assertiveness = st.slider("Assertiveness", 1, 10, default_assertiveness)
    creativity = st.slider("Creativity", 0, 10, default_creativity)

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

    # Save/Load Personas Section
    st.markdown("### 💾 Save/Load Personas")
    
    # Clear loaded persona button
    if "loaded_config" in st.session_state:
        if st.button("🔄 Return to Presets"):
            del st.session_state.loaded_config
            st.session_state.selected_preset = PRESETS[0].key
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        persona_save_name = st.text_input("Persona Name to Save", placeholder="e.g., My Custom Mage")
        if st.button("💾 Save Persona") and persona_save_name.strip():
            try:
                # Create personas directory if it doesn't exist
                personas_dir = os.path.join(os.getcwd(), "saved_personas")
                os.makedirs(personas_dir, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{persona_save_name.replace(' ', '_')}_{timestamp}.json"
                filepath = os.path.join(personas_dir, filename)
                
                cfg.save_to_file(filepath)
                st.success(f"✅ Persona saved as: {filename}")
                
                # Clear the input
                st.session_state.save_name = ""
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save persona: {e}")
    
    with col2:
        # Get list of saved personas
        personas_dir = os.path.join(os.getcwd(), "saved_personas")
        saved_personas = []
        if os.path.exists(personas_dir):
            saved_personas = [f for f in os.listdir(personas_dir) if f.endswith('.json')]
        
        if saved_personas:
            selected_persona = st.selectbox("Load Saved Persona", ["Choose a persona..."] + saved_personas)
            if st.button("📂 Load Persona") and selected_persona != "Choose a persona...":
                try:
                    filepath = os.path.join(personas_dir, selected_persona)
                    loaded_cfg = PersonaConfig.load_from_file(filepath)
                    
                    # Update session state to reflect loaded persona
                    st.session_state.selected_preset = "custom_loaded"
                    st.session_state.loaded_config = loaded_cfg
                    
                    st.success(f"✅ Loaded persona: {selected_persona}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to load persona: {e}")
        else:
            st.info("No saved personas found. Save one first!")

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
                        for chunk in selected_provider.chat_stream(
                            model=selected_model,
                            system_prompt=system_prompt,
                            messages=st.session_state.msgs
                        ):
                            accumulated_content += chunk
                            message_placeholder.write(accumulated_content)
                    except Exception as e:
                        accumulated_content = f"Error during streaming: {e}"
                        message_placeholder.write(accumulated_content)

                    reply = accumulated_content
            else:
                # Non-streaming response
                reply = selected_provider.chat(
                    model=selected_model,
                    system_prompt=system_prompt,
                    messages=st.session_state.msgs
                )
                st.chat_message("assistant", avatar=avatar).write(reply)
        except Exception as e:
            reply = f"Error talking to {selected_provider_name}: {e}"
            st.chat_message("assistant", avatar=avatar).write(reply)

        st.session_state.msgs.append({"role": "assistant", "content": reply})
