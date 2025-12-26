"""
Enhanced styling and theming system for the persona chat app.
"""
from __future__ import annotations
import streamlit as st
from typing import Dict, Any, Optional
from dataclasses import dataclass
from personas.presets import CLASS_FLAVOR


@dataclass
class ThemeColors:
    """Color scheme for a theme."""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str
    success: str
    warning: str
    error: str
    info: str


@dataclass
class Theme:
    """Complete theme configuration."""
    name: str
    colors: ThemeColors
    fonts: Dict[str, str]
    spacing: Dict[str, str]
    border_radius: str
    shadows: Dict[str, str]


# Predefined color schemes
LIGHT_THEME = ThemeColors(
    primary="#1f77b4",
    secondary="#ff7f0e",
    accent="#2ca02c",
    background="#ffffff",
    surface="#f8f9fa",
    text="#212529",
    text_secondary="#6c757d",
    border="#dee2e6",
    success="#28a745",
    warning="#ffc107",
    error="#dc3545",
    info="#17a2b8"
)

DARK_THEME = ThemeColors(
    primary="#4dabf7",
    secondary="#ff922b",
    accent="#51cf66",
    background="#121212",
    surface="#1e1e1e",
    text="#ffffff",
    text_secondary="#adb5bd",
    border="#495057",
    success="#40c057",
    warning="#ffd43b",
    error="#fa5252",
    info="#339af0"
)

# WoW Class-specific themes
CLASS_THEMES = {
    "Mage": ThemeColors(
        primary="#3b82f6",  # Blue
        secondary="#1e40af",
        accent="#60a5fa",
        background="#ffffff",
        surface="#eff6ff",
        text="#1e3a8a",
        text_secondary="#3b82f6",
        border="#93c5fd",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#3b82f6"
    ),
    "Warrior": ThemeColors(
        primary="#dc2626",  # Red
        secondary="#991b1b",
        accent="#f87171",
        background="#ffffff",
        surface="#fef2f2",
        text="#7f1d1d",
        text_secondary="#dc2626",
        border="#fca5a5",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#dc2626"
    ),
    "Paladin": ThemeColors(
        primary="#eab308",  # Gold
        secondary="#a16207",
        accent="#facc15",
        background="#ffffff",
        surface="#fefce8",
        text="#713f12",
        text_secondary="#eab308",
        border="#fde047",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#eab308"
    ),
    "Rogue": ThemeColors(
        primary="#16a34a",  # Green
        secondary="#14532d",
        accent="#4ade80",
        background="#ffffff",
        surface="#f0fdf4",
        text="#14532d",
        text_secondary="#16a34a",
        border="#86efac",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#16a34a"
    ),
    "Priest": ThemeColors(
        primary="#7c3aed",  # Purple
        secondary="#581c87",
        accent="#a78bfa",
        background="#ffffff",
        surface="#faf5ff",
        text="#581c87",
        text_secondary="#7c3aed",
        border="#c4b5fd",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#7c3aed"
    ),
    "Shaman": ThemeColors(
        primary="#0891b2",  # Teal
        secondary="#164e63",
        accent="#22d3ee",
        background="#ffffff",
        surface="#ecfeff",
        text="#164e63",
        text_secondary="#0891b2",
        border="#67e8f9",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#0891b2"
    ),
    "Druid": ThemeColors(
        primary="#15803d",  # Forest Green
        secondary="#14532d",
        accent="#22c55e",
        background="#ffffff",
        surface="#f0fdf4",
        text="#14532d",
        text_secondary="#15803d",
        border="#86efac",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#15803d"
    ),
    "Hunter": ThemeColors(
        primary="#a16207",  # Brown
        secondary="#78350f",
        accent="#d97706",
        background="#ffffff",
        surface="#fffbeb",
        text="#78350f",
        text_secondary="#a16207",
        border="#fcd34d",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#a16207"
    ),
    "Warlock": ThemeColors(
        primary="#7c2d12",  # Dark Red
        secondary="#450a0a",
        accent="#dc2626",
        background="#ffffff",
        surface="#fef2f2",
        text="#450a0a",
        text_secondary="#7c2d12",
        border="#fca5a5",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#7c2d12"
    ),
    "Death Knight": ThemeColors(
        primary="#1f2937",  # Dark Gray
        secondary="#111827",
        accent="#374151",
        background="#ffffff",
        surface="#f9fafb",
        text="#111827",
        text_secondary="#1f2937",
        border="#d1d5db",
        success="#10b981",
        warning="#f59e0b",
        error="#ef4444",
        info="#1f2937"
    )
}


class ThemeManager:
    """Manages application theming and styling."""

    def __init__(self):
        self.themes = {
            "light": Theme(
                name="Light",
                colors=LIGHT_THEME,
                fonts={
                    "primary": "system-ui, -apple-system, sans-serif",
                    "mono": "Monaco, 'Cascadia Code', 'Roboto Mono', monospace"
                },
                spacing={
                    "xs": "0.25rem",
                    "sm": "0.5rem",
                    "md": "1rem",
                    "lg": "1.5rem",
                    "xl": "2rem",
                    "xxl": "3rem"
                },
                border_radius="0.5rem",
                shadows={
                    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
                }
            ),
            "dark": Theme(
                name="Dark",
                colors=DARK_THEME,
                fonts={
                    "primary": "system-ui, -apple-system, sans-serif",
                    "mono": "Monaco, 'Cascadia Code', 'Roboto Mono', monospace"
                },
                spacing={
                    "xs": "0.25rem",
                    "sm": "0.5rem",
                    "md": "1rem",
                    "lg": "1.5rem",
                    "xl": "2rem",
                    "xxl": "3rem"
                },
                border_radius="0.5rem",
                shadows={
                    "sm": "0 1px 2px 0 rgba(255, 255, 255, 0.05)",
                    "md": "0 4px 6px -1px rgba(255, 255, 255, 0.1)",
                    "lg": "0 10px 15px -3px rgba(255, 255, 255, 0.1)"
                }
            )
        }

    def get_theme(self, theme_name: str = "light") -> Theme:
        """Get a theme by name."""
        return self.themes.get(theme_name, self.themes["light"])

    def get_class_theme(self, class_name: str) -> ThemeColors:
        """Get theme colors for a WoW class."""
        return CLASS_THEMES.get(class_name, LIGHT_THEME)

    def apply_theme_css(self, theme: Theme, class_theme: Optional[ThemeColors] = None):
        """Apply theme as custom CSS."""
        colors = class_theme or theme.colors

        css = f"""
        <style>
        :root {{
            --primary-color: {colors.primary};
            --secondary-color: {colors.secondary};
            --accent-color: {colors.accent};
            --background-color: {colors.background};
            --surface-color: {colors.surface};
            --text-color: {colors.text};
            --text-secondary-color: {colors.text_secondary};
            --border-color: {colors.border};
            --success-color: {colors.success};
            --warning-color: {colors.warning};
            --error-color: {colors.error};
            --info-color: {colors.info};
            --border-radius: {theme.border_radius};
            --font-primary: {theme.fonts['primary']};
            --font-mono: {theme.fonts['mono']};
            --shadow-sm: {theme.shadows['sm']};
            --shadow-md: {theme.shadows['md']};
            --shadow-lg: {theme.shadows['lg']};
        }}

        /* Global styling */
        .main {{
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: var(--font-primary);
        }}

        /* Streamlit component overrides */
        .stTextInput > div > div > input {{
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            background-color: var(--surface-color);
            color: var(--text-color);
        }}

        .stSelectbox > div > div {{
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            background-color: var(--surface-color);
        }}

        .stButton > button {{
            border-radius: var(--border-radius);
            border: 1px solid var(--primary-color);
            background-color: var(--primary-color);
            color: white;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .stButton > button:hover {{
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}

        /* Chat message styling */
        .stChatMessage {{
            border-radius: var(--border-radius);
            margin: var(--spacing-sm) 0;
            padding: var(--spacing-md);
            box-shadow: var(--shadow-sm);
        }}

        .stChatMessage[data-testid="user-message"] {{
            background-color: var(--surface-color);
            border-left: 4px solid var(--primary-color);
        }}

        .stChatMessage[data-testid="assistant-message"] {{
            background-color: var(--surface-color);
            border-left: 4px solid var(--accent-color);
        }}

        /* Sidebar styling */
        .css-1d391kg {{
            background-color: var(--surface-color);
            border-right: 1px solid var(--border-color);
        }}

        /* Expander styling */
        .streamlit-expanderHeader {{
            background-color: var(--surface-color);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }}

        /* Code blocks */
        .stCodeBlock {{
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            background-color: var(--surface-color);
        }}

        pre {{
            background-color: var(--surface-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: var(--border-radius) !important;
        }}

        code {{
            background-color: var(--surface-color) !important;
            color: var(--text-color) !important;
            font-family: var(--font-mono) !important;
        }}

        /* Success/Warning/Error messages */
        .stSuccess {{
            background-color: rgba(40, 167, 69, 0.1);
            border-left: 4px solid var(--success-color);
            color: var(--success-color);
        }}

        .stWarning {{
            background-color: rgba(255, 193, 7, 0.1);
            border-left: 4px solid var(--warning-color);
            color: var(--warning-color);
        }}

        .stError {{
            background-color: rgba(220, 53, 69, 0.1);
            border-left: 4px solid var(--error-color);
            color: var(--error-color);
        }}

        .stInfo {{
            background-color: rgba(23, 162, 184, 0.1);
            border-left: 4px solid var(--info-color);
            color: var(--info-color);
        }}

        /* Custom conversation styling */
        .conversation-item {{
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            margin: var(--spacing-xs) 0;
            transition: all 0.2s ease;
        }}

        .conversation-item:hover {{
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
        }}

        .persona-badge {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius);
            font-weight: bold;
            font-size: 0.875rem;
            display: inline-block;
            margin: var(--spacing-xs) 0;
        }}

        /* Avatar styling */
        .avatar-large {{
            font-size: 2rem;
            filter: drop-shadow(var(--shadow-sm));
        }}

        /* Provider badges */
        .provider-badge {{
            display: inline-block;
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius);
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .provider-badge.ollama {{
            background-color: var(--accent-color);
            color: white;
        }}

        .provider-badge.openai {{
            background-color: #10a37f;
            color: white;
        }}

        .provider-badge.anthropic {{
            background-color: #d97706;
            color: white;
        }}

        .provider-badge.google {{
            background-color: #ea4335;
            color: white;
        }}

        .provider-badge.xai {{
            background-color: #000000;
            color: white;
        }}

        .provider-badge.deepseek {{
            background-color: #7c3aed;
            color: white;
        }}

        /* Loading animation */
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .loading {{
            animation: pulse 2s infinite;
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            .main {{
                padding: var(--spacing-sm);
            }}

            .stChatMessage {{
                margin: var(--spacing-xs) 0;
                padding: var(--spacing-sm);
            }}
        }}
        </style>
        """

        st.markdown(css, unsafe_allow_html=True)

    def get_provider_badge_class(self, provider_name: str) -> str:
        """Get CSS class for provider badge."""
        return f"provider-badge {provider_name.lower()}"

    def create_persona_badge(self, persona_name: str, cls: str, spec: str, mode: str, avatar: str) -> str:
        """Create a styled persona badge."""
        return f"""
        <div class="persona-badge">
            {avatar} {persona_name} | {cls} / {spec} | {mode}
        </div>
        """


# Global theme manager instance
theme_manager = ThemeManager()