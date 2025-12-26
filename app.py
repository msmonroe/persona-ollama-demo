from __future__ import annotations
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st

from ollama.client import chat as ollama_chat, chat_stream, health_check, OllamaConnectionError
from models import registry
from personas.presets import PRESETS, CLASS_FLAVOR, SPEC_BEHAVIOR, CLASS_AVATAR
from personas.prompt_builder import PersonaConfig, build_system_prompt, PersonaValidationError, PersonaValidationError
from conversations import Conversation, ConversationManager
from themes import theme_manager
from instrumentation import (
    instrumentation, log_chat_request, log_chat_response, log_provider_health_check,
    create_debug_panel, export_diagnostics
)

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
DEFAULT_VERSION = os.getenv("APP_VERSION", "Persona Creator v1.3")

# Initialize conversation manager
conversation_manager = ConversationManager()

# Check provider connection on startup
@st.cache_data(ttl=30)
def check_provider_status(provider_name: str):
    """Check if the selected provider is accessible (cached for 30 seconds)."""
    start_time = time.time()
    try:
        provider = registry.get_provider(provider_name)
        if provider and provider.health_check():
            duration = time.time() - start_time
            log_provider_health_check(provider_name, True, duration)
            return True, None
        else:
            duration = time.time() - start_time
            log_provider_health_check(provider_name, False, duration, Exception("Health check failed"))
            return False, f"Cannot connect to {provider_name}"
    except Exception as e:
        duration = time.time() - start_time
        log_provider_health_check(provider_name, False, duration, e)
        return False, str(e)

# Provider health check will be done after provider selection
provider_healthy = True
provider_error = None

# Enhanced page config with theme support
st.set_page_config(
    page_title="Persona Creator + Multi-Model AI",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/msmonroe/persona-ollama-demo',
        'Report a bug': 'https://github.com/msmonroe/persona-ollama-demo/issues',
        'About': '''
        ## Persona Creator Demo (WoW-style) + Multi-Model AI 🤖

        A demo that lets you pick an AI **Class** + **Spec** (WoW-style), customize visual avatars,
        and generates a **system prompt** that steers multiple AI models.

        **Features:**
        - WoW-style Class/Spec persona builder
        - Multi-model AI support (Ollama, OpenAI, Anthropic, Google, xAI, DeepSeek)
        - Conversation management with save/load
        - Enhanced theming and styling
        - Real-time streaming responses
        '''
    }
)

st.title("🎭 Persona Creator Demo (WoW-style) + Multi-Model AI 🤖")

def init_state():
    if "msgs" not in st.session_state:
        st.session_state.msgs = []
    if "selected_preset" not in st.session_state:
        st.session_state.selected_preset = PRESETS[0].key
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = None
    if "conversation_title" not in st.session_state:
        st.session_state.conversation_title = ""
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "use_class_theme" not in st.session_state:
        st.session_state.use_class_theme = True

# Initialize state first
init_state()

# Theme selection and application
col_theme1, col_theme2, col_theme3 = st.columns([1, 1, 2])

with col_theme1:
    selected_theme = st.selectbox(
        "🎨 Theme",
        options=["light", "dark"],
        index=["light", "dark"].index(st.session_state.theme),
        help="Choose your preferred color theme"
    )
    st.session_state.theme = selected_theme

with col_theme2:
    use_class_theme = st.checkbox(
        "Class Colors",
        value=st.session_state.use_class_theme,
        help="Use WoW class-specific colors"
    )
    st.session_state.use_class_theme = use_class_theme

with col_theme3:
    st.caption("💡 Tip: Try different themes and class colors for unique experiences!")

# Apply theme (will be updated after persona selection)
current_theme = theme_manager.get_theme(st.session_state.theme)
theme_manager.apply_theme_css(current_theme)

left, right = st.columns([1, 2])

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
        default_formality = loaded_cfg.formality
        default_empathy = loaded_cfg.empathy
        default_technical_level = loaded_cfg.technical_level
        default_patience = loaded_cfg.patience
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
        default_formality = preset.formality
        default_empathy = preset.empathy
        default_technical_level = preset.technical_level
        default_patience = preset.patience
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
        default_formality = preset.formality
        default_empathy = preset.empathy
        default_technical_level = preset.technical_level
        default_patience = preset.patience
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
    ) or "Ollama"  # Default fallback

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
    formality = st.slider("Formality", 0, 10, default_formality)
    empathy = st.slider("Empathy", 0, 10, default_empathy)
    technical_level = st.slider("Technical Level", 0, 10, default_technical_level)
    patience = st.slider("Patience", 0, 10, default_patience)

    cfg = PersonaConfig(
        version_codename=version_codename,
        cls=cls,
        spec=spec,
        mode=mode,
        verbosity=verbosity,
        humor=humor,
        assertiveness=assertiveness,
        creativity=creativity,
        formality=formality,
        empathy=empathy,
        technical_level=technical_level,
        patience=patience,
        name=persona_name,
        avatar=avatar,
    )
    system_prompt = build_system_prompt(cfg)

    # Apply class-specific theme colors if enabled
    if st.session_state.use_class_theme:
        class_colors = theme_manager.get_class_theme(cls)
        theme_manager.apply_theme_css(current_theme, class_colors)

    # Enhanced Persona Badge with styling
    st.markdown("### 👤 Persona Badge")
    persona_badge_html = theme_manager.create_persona_badge(
        persona_name or version_codename,
        cls, spec, mode, avatar
    )
    st.markdown(persona_badge_html, unsafe_allow_html=True)

    # Provider badge
    provider_badge_class = theme_manager.get_provider_badge_class(selected_provider_name)
    st.markdown(f'<span class="{provider_badge_class}">{selected_provider_name}</span>', unsafe_allow_html=True)

    with st.expander("📝 Generated system prompt"):
        st.code(system_prompt, language="text")

    if st.button("New Chat"):
        # Save current conversation if it has messages
        if st.session_state.current_conversation and st.session_state.msgs:
            conversation_manager.save_conversation(st.session_state.current_conversation)
            st.success("💾 Previous conversation saved!")

        # Create new conversation
        persona_display_name = persona_name or f"{cls} {spec}"
        st.session_state.current_conversation = Conversation.new(
            persona_name=persona_display_name,
            persona_class=cls,
            persona_spec=spec,
            provider_name=selected_provider_name,
            model_name=selected_model
        )
        st.session_state.msgs = []
        st.session_state.conversation_title = ""
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
                instrumentation.log_operation("persona_save", True, persona_name=persona_save_name, filepath=filename)
                st.success(f"✅ Persona saved as: {filename}")
                
                # Clear the input
                st.session_state.save_name = ""
                st.rerun()
            except Exception as e:
                instrumentation.log_operation("persona_save", False, error=e, persona_name=persona_save_name)
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
                    
                    instrumentation.log_operation("persona_load", True, persona_file=selected_persona)
                    st.success(f"✅ Loaded persona: {selected_persona}")
                    st.rerun()
                except Exception as e:
                    instrumentation.log_operation("persona_load", False, error=e, persona_file=selected_persona)
                    st.error(f"❌ Failed to load persona: {e}")
        else:
            st.info("No saved personas found. Save one first!")

    # Conversation Management Section
    st.markdown("### 💬 Conversation Management")

    # New Conversation / Save Current
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("🆕 New Conversation"):
            # Save current conversation if it has messages
            if st.session_state.current_conversation and st.session_state.msgs:
                conversation_manager.save_conversation(st.session_state.current_conversation)
                instrumentation.log_operation("conversation_save", True, conversation_id=st.session_state.current_conversation.id)
                st.success("💾 Previous conversation saved!")

            # Create new conversation
            persona_display_name = persona_name or f"{cls} {spec}"
            st.session_state.current_conversation = Conversation.new(
                persona_name=persona_display_name,
                persona_class=cls,
                persona_spec=spec,
                provider_name=selected_provider_name,
                model_name=selected_model
            )
            instrumentation.log_operation("conversation_new", True, persona_name=persona_display_name)
            st.session_state.msgs = []
            st.session_state.conversation_title = ""
            st.rerun()

    with col2:
        if st.session_state.current_conversation and st.session_state.msgs:
            # Auto-generate title from first user message
            if not st.session_state.conversation_title and st.session_state.msgs:
                first_user_msg = next((msg["content"] for msg in st.session_state.msgs if msg["role"] == "user"), "")
                if first_user_msg:
                    # Truncate to 50 chars and clean
                    title = first_user_msg[:50].replace("\n", " ").strip()
                    if len(first_user_msg) > 50:
                        title += "..."
                    st.session_state.conversation_title = title
                    st.session_state.current_conversation.title = title

            conversation_title_input = st.text_input(
                "Conversation Title",
                value=st.session_state.conversation_title,
                placeholder="Enter a title for this conversation"
            )

            if st.button("💾 Save Conversation") and conversation_title_input.strip():
                st.session_state.current_conversation.title = conversation_title_input.strip()
                filepath = conversation_manager.save_conversation(st.session_state.current_conversation)
                st.success(f"✅ Conversation saved!")
                st.session_state.conversation_title = conversation_title_input.strip()

    with col3:
        # Load conversation dropdown
        saved_conversations = conversation_manager.list_conversations()
        if saved_conversations:
            conversation_options = ["Choose a conversation..."] + [f"{c.title} ({c.updated_at[:10]})" for c in saved_conversations]
            selected_conversation_display = st.selectbox(
                "Load Conversation",
                options=conversation_options
            )

            if selected_conversation_display != "Choose a conversation...":
                # Find the actual conversation
                selected_idx = conversation_options.index(selected_conversation_display) - 1
                selected_conv = saved_conversations[selected_idx]

                if st.button("📂 Load Selected"):
                    # Save current conversation if it has messages
                    if st.session_state.current_conversation and st.session_state.msgs:
                        conversation_manager.save_conversation(st.session_state.current_conversation)
                        instrumentation.log_operation("conversation_save", True, conversation_id=st.session_state.current_conversation.id)
                        st.info("💾 Previous conversation saved!")

                    # Load selected conversation
                    st.session_state.current_conversation = selected_conv
                    st.session_state.msgs = selected_conv.get_messages_for_chat()
                    st.session_state.conversation_title = selected_conv.title
                    instrumentation.log_operation("conversation_load", True, conversation_id=selected_conv.id, message_count=len(st.session_state.msgs))
                    st.success(f"✅ Loaded conversation: {selected_conv.title}")
                    st.rerun()
        else:
            st.info("No saved conversations yet!")

    # Conversation History
    if saved_conversations:
        with st.expander("📚 Conversation History", expanded=False):
            for conv in saved_conversations[:10]:  # Show last 10
                # Create styled conversation item
                conversation_html = f"""
                <div class="conversation-item">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                        <div style="flex: 1;">
                            <strong style="color: var(--text-color); font-size: 1.1em;">{conv.title}</strong>
                            <div style="color: var(--text-secondary-color); font-size: 0.9em; margin-top: 0.25rem;">
                                {conv.persona_name} • {conv.provider_name}/{conv.model_name}
                            </div>
                            <div style="color: var(--text-secondary-color); font-size: 0.8em;">
                                {conv.get_summary()}
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem;">
                            <button style="
                                background-color: var(--primary-color);
                                color: white;
                                border: none;
                                border-radius: var(--border-radius);
                                padding: 0.25rem 0.75rem;
                                font-size: 0.8em;
                                cursor: pointer;
                                transition: all 0.2s ease;
                            " onclick="javascript:void(0)" id="load_{conv.id}">📂 Load</button>
                            <button style="
                                background-color: var(--error-color);
                                color: white;
                                border: none;
                                border-radius: var(--border-radius);
                                padding: 0.25rem 0.75rem;
                                font-size: 0.8em;
                                cursor: pointer;
                                transition: all 0.2s ease;
                            " onclick="javascript:void(0)" id="delete_{conv.id}">🗑️ Delete</button>
                        </div>
                    </div>
                </div>
                """
                st.markdown(conversation_html, unsafe_allow_html=True)

                # Handle button clicks (since HTML buttons don't work directly in Streamlit)
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("📂 Load", key=f"load_{conv.id}", help=f"Load conversation: {conv.title}"):
                        # Save current conversation if it has messages
                        if st.session_state.current_conversation and st.session_state.msgs:
                            conversation_manager.save_conversation(st.session_state.current_conversation)

                        st.session_state.current_conversation = conv
                        st.session_state.msgs = conv.get_messages_for_chat()
                        st.session_state.conversation_title = conv.title
                        st.success(f"✅ Loaded: {conv.title}")
                        st.rerun()

                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{conv.id}", help=f"Delete conversation: {conv.title}"):
                        if conversation_manager.delete_conversation(conv.id):
                            st.success("🗑️ Conversation deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete conversation!")

    # Export Current Conversation
    if st.session_state.current_conversation and st.session_state.msgs:
        st.markdown("### 📤 Export Conversation")
        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            if st.button("📄 Export as JSON"):
                export_data = conversation_manager.export_conversation(st.session_state.current_conversation.id, "json")
                if export_data:
                    st.download_button(
                        label="📥 Download JSON",
                        data=export_data,
                        file_name=f"{st.session_state.current_conversation.title.replace(' ', '_')}.json",
                        mime="application/json"
                    )

        with export_col2:
            if st.button("📝 Export as Text"):
                export_data = conversation_manager.export_conversation(st.session_state.current_conversation.id, "txt")
                if export_data:
                    st.download_button(
                        label="📥 Download TXT",
                        data=export_data,
                        file_name=f"{st.session_state.current_conversation.title.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )

        with export_col3:
            if st.button("📖 Export as Markdown"):
                export_data = conversation_manager.export_conversation(st.session_state.current_conversation.id, "markdown")
                if export_data:
                    st.download_button(
                        label="📥 Download MD",
                        data=export_data,
                        file_name=f"{st.session_state.current_conversation.title.replace(' ', '_')}.md",
                        mime="text/markdown"
                    )

with right:
    st.subheader("Chat")

    # Show current conversation info
    if st.session_state.current_conversation:
        st.caption(f"Current: {st.session_state.current_conversation.title}")
    else:
        st.caption("No active conversation - start chatting to create one!")

    # Display chat messages with enhanced styling
    for i, m in enumerate(st.session_state.msgs):
        if m["role"] == "assistant":
            # Enhanced assistant message with theme styling
            assistant_html = f"""
            <div style="
                background-color: var(--surface-color);
                border: 1px solid var(--border-color);
                border-left: 4px solid var(--accent-color);
                border-radius: var(--border-radius);
                padding: var(--spacing-md);
                margin: var(--spacing-sm) 0;
                box-shadow: var(--shadow-sm);
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: var(--spacing-sm);
                    left: var(--spacing-sm);
                    font-size: 1.2em;
                    opacity: 0.8;
                ">{avatar}</div>
                <div style="
                    margin-left: 2.5rem;
                    color: var(--text-color);
                    line-height: 1.5;
                ">{m["content"]}</div>
            </div>
            """
            st.markdown(assistant_html, unsafe_allow_html=True)
        else:
            # Enhanced user message with theme styling
            user_html = f"""
            <div style="
                background-color: var(--surface-color);
                border: 1px solid var(--border-color);
                border-left: 4px solid var(--primary-color);
                border-radius: var(--border-radius);
                padding: var(--spacing-md);
                margin: var(--spacing-sm) 0;
                box-shadow: var(--shadow-sm);
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: var(--spacing-sm);
                    left: var(--spacing-sm);
                    font-size: 1.2em;
                    opacity: 0.8;
                ">👤</div>
                <div style="
                    margin-left: 2.5rem;
                    color: var(--text-color);
                    line-height: 1.5;
                ">{m["content"]}</div>
            </div>
            """
            st.markdown(user_html, unsafe_allow_html=True)

    user_text = st.chat_input("Ask something (try an accounting question)…")
    if user_text:
        # Log chat request
        log_chat_request(selected_provider_name, selected_model, len(st.session_state.msgs), streaming_enabled)

        # Create conversation if none exists
        if not st.session_state.current_conversation:
            persona_display_name = persona_name or f"{cls} {spec}"
            st.session_state.current_conversation = Conversation.new(
                persona_name=persona_display_name,
                persona_class=cls,
                persona_spec=spec,
                provider_name=selected_provider_name,
                model_name=selected_model
            )

        # Add user message
        st.session_state.msgs.append({"role": "user", "content": user_text})
        st.session_state.current_conversation.add_message("user", user_text, "👤")
        st.chat_message("user", avatar="👤").write(user_text)

        try:
            if streaming_enabled:
                # Simplified streaming response using standard Streamlit chat
                with st.chat_message("assistant", avatar=avatar):
                    message_placeholder = st.empty()
                    accumulated_content = ""

                    try:
                        start_time = time.time()
                        for chunk in selected_provider.chat_stream(
                            model=selected_model,
                            system_prompt=system_prompt,
                            messages=st.session_state.msgs
                        ):
                            accumulated_content += chunk
                            message_placeholder.write(accumulated_content)
                        duration = time.time() - start_time
                        log_chat_response(selected_provider_name, selected_model, True,
                                        len(accumulated_content), duration=duration)
                    except Exception as e:
                        duration = time.time() - start_time
                        accumulated_content = f"Error during streaming: {e}"
                        message_placeholder.write(accumulated_content)
                        log_chat_response(selected_provider_name, selected_model, False,
                                        duration=duration, error=e)

                    reply = accumulated_content
            else:
                # Non-streaming response with enhanced styling
                start_time = time.time()
                try:
                    reply = selected_provider.chat(
                        model=selected_model,
                        system_prompt=system_prompt,
                        messages=st.session_state.msgs
                    )
                    duration = time.time() - start_time
                    log_chat_response(selected_provider_name, selected_model, True,
                                    len(reply), duration=duration)
                except Exception as e:
                    duration = time.time() - start_time
                    reply = f"Error talking to {selected_provider_name}: {e}"
                    log_chat_response(selected_provider_name, selected_model, False,
                                    duration=duration, error=e)
                assistant_reply_html = f"""
                <div style="
                    background-color: var(--surface-color);
                    border: 1px solid var(--border-color);
                    border-left: 4px solid var(--accent-color);
                    border-radius: var(--border-radius);
                    padding: var(--spacing-md);
                    margin: var(--spacing-sm) 0;
                    box-shadow: var(--shadow-sm);
                    position: relative;
                ">
                    <div style="
                        position: absolute;
                        top: var(--spacing-sm);
                        left: var(--spacing-sm);
                        font-size: 1.2em;
                        opacity: 0.8;
                    ">{avatar}</div>
                    <div style="
                        margin-left: 2.5rem;
                        color: var(--text-color);
                        line-height: 1.5;
                    ">{reply}</div>
                </div>
                """
                st.markdown(assistant_reply_html, unsafe_allow_html=True)
        except Exception as e:
            reply = f"Error talking to {selected_provider_name}: {e}"
            log_chat_response(selected_provider_name, selected_model, False, error=e)
            error_reply_html = f"""
            <div style="
                background-color: var(--surface-color);
                border: 1px solid var(--border-color);
                border-left: 4px solid var(--error-color);
                border-radius: var(--border-radius);
                padding: var(--spacing-md);
                margin: var(--spacing-sm) 0;
                box-shadow: var(--shadow-sm);
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: var(--spacing-sm);
                    left: var(--spacing-sm);
                    font-size: 1.2em;
                    opacity: 0.8;
                ">{avatar}</div>
                <div style="
                    margin-left: 2.5rem;
                    color: var(--error-color);
                    line-height: 1.5;
                ">{reply}</div>
            </div>
            """
            st.markdown(error_reply_html, unsafe_allow_html=True)

        # Add assistant message
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        st.session_state.current_conversation.add_message("assistant", reply, avatar)

# Debug and Diagnostics Panel
st.markdown("---")
create_debug_panel()

# Export diagnostics for support
st.markdown("### 📊 Export Diagnostics")
if st.button("📤 Export Diagnostics Data"):
    diagnostics_json = export_diagnostics()
    st.download_button(
        label="📥 Download Diagnostics",
        data=diagnostics_json,
        file_name=f"persona_creator_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
