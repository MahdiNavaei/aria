"""ARIA Control Room - Professional Bilingual UI.

A human-centered, bilingual (Persian/English) dashboard for the ARIA agent.
Features RTL support, dark mode, real-time updates, and HITL controls.

Usage:
    streamlit run src/aria/ui/app.py --server.port 8501

Author: Mahdi Navaei
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st

from aria.config import get_settings
from aria.ui.components import (
    add_message,
    render_activity_log,
    render_agent_controls,
    render_browser_controls,
    render_browser_view,
    render_chat,
    render_goal_input,
    render_hitl_panel,
    render_status_bar,
    render_step_panel,
)
from aria.ui.i18n import get_direction, get_language, is_rtl, set_language, t

# Auto-refresh configuration
AUTO_REFRESH_INTERVAL = 2  # seconds
AUTO_REFRESH_ENABLED_STATUSES = {"running", "waiting_human"}

# =============================================================================
# Style Loading
# =============================================================================

def _load_styles() -> None:
    """Load CSS styles based on current language and theme."""
    # #region agent log
    import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"D","location":"app.py:_load_styles","message":"styles_load_start","data":{"lang":st.session_state.get("language","?"),"theme":st.session_state.get("theme","?")},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion
    styles_dir = Path(__file__).parent / "styles"

    # Base theme (always loaded)
    theme_path = styles_dir / "theme.css"
    if theme_path.exists():
        # #region agent log
        open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"D","location":"app.py:theme_css","message":"theme_css_loaded","data":{"path":str(theme_path),"size":theme_path.stat().st_size},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        st.markdown(
            f"<style>{theme_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    
    # Get current theme
    theme = st.session_state.get("theme", "light")
    
    # Light mode - Beautiful modern design
    if theme == "light":
        light_css = """
        /* ========== LIGHT MODE - MODERN & VIBRANT ========== */
        :root,
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"] {
            --color-bg-primary: #F8FAFC !important;
            --color-bg-secondary: #F1F5F9 !important;
            --color-bg-card: #FFFFFF !important;
            --color-text-primary: #0F172A !important;
            --color-text-secondary: #475569 !important;
            --color-text-muted: #94A3B8 !important;
            --color-accent: #F59E0B !important;
            --color-accent-light: #FEF3C7 !important;
            
            background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 50%, #F1F5F9 100%) !important;
            color: #0F172A !important;
        }
        
        /* Main container with subtle pattern */
        .stApp, [data-testid="stAppViewContainer"] {
            background: 
                radial-gradient(circle at 20% 80%, rgba(251, 191, 36, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(14, 165, 233, 0.06) 0%, transparent 50%),
                linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 50%, #F1F5F9 100%) !important;
        }
        
        /* Sidebar - Clean glass effect */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.04) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #1E293B !important;
        }
        
        /* Headings with accent underline */
        h1, h2, h3, h4, h5, h6 {
            color: #0F172A !important;
            font-weight: 700 !important;
        }
        
        /* Title styling */
        [data-testid="stMarkdownContainer"] h1 {
            background: linear-gradient(135deg, #0F172A 0%, #334155 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        p, span, label {
            color: #475569 !important;
        }
        
        div {
            color: #334155 !important;
        }
        
        /* Metric cards - Elevated with shadow */
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            border: 1px solid rgba(0, 0, 0, 0.04) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.05),
                0 10px 15px -3px rgba(0, 0, 0, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 
                0 10px 20px -5px rgba(0, 0, 0, 0.08),
                0 20px 25px -10px rgba(0, 0, 0, 0.06) !important;
        }
        
        .stMetric label {
            color: #64748B !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        
        .stMetric [data-testid="stMetricValue"] {
            color: #0F172A !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
        }
        
        /* Inputs - Modern with focus glow */
        .stTextInput input, .stTextArea textarea {
            background: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            transition: all 0.2s ease !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #F59E0B !important;
            box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.15) !important;
            outline: none !important;
        }
        
        /* Buttons - Vibrant gradient */
        .stButton > button {
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35) !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(245, 158, 11, 0.45) !important;
        }
        
        /* Secondary buttons */
        .stButton > button[kind="secondary"] {
            background: linear-gradient(145deg, #FFFFFF 0%, #F1F5F9 100%) !important;
            color: #334155 !important;
            border: 2px solid #E2E8F0 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        }
        
        /* Dividers */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, #CBD5E1, transparent) !important;
            margin: 24px 0 !important;
        }
        
        /* Header */
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        
        /* Cards/containers */
        [data-testid="stExpander"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        }
        """
        st.markdown(f"<style>{light_css}</style>", unsafe_allow_html=True)

    # Animations
    animations_path = styles_dir / "animations.css"
    if animations_path.exists():
        st.markdown(
            f"<style>{animations_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

    # RTL styles for Persian/Arabic
    if is_rtl():
        rtl_path = styles_dir / "rtl.css"
        if rtl_path.exists():
            st.markdown(
                f"<style>{rtl_path.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True,
            )

    # Dark mode - inject CSS variables directly (no JavaScript required)
    # #region agent log
    open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"F","location":"app.py:dark_mode","message":"dark_mode_check","data":{"theme":theme,"should_load_dark":theme=="dark"},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion
    if theme == "dark":
        # #region agent log
        open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"F","location":"app.py:dark_css","message":"dark_css_INJECTING_DIRECTLY","data":{"method":"inline_css"},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        # Dark mode - Premium elegant design
        dark_css = """
        /* ========== DARK MODE - PREMIUM & ELEGANT ========== */
        :root,
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"] {
            --color-bg-primary: #0C0C0E !important;
            --color-bg-secondary: #141416 !important;
            --color-bg-card: #1C1C1F !important;
            --color-text-primary: #F8FAFC !important;
            --color-text-secondary: #94A3B8 !important;
            --color-accent: #FBBF24 !important;
            --color-accent-glow: rgba(251, 191, 36, 0.2) !important;
            
            background: linear-gradient(135deg, #0C0C0E 0%, #141416 50%, #18181B 100%) !important;
            color: #F8FAFC !important;
        }
        
        /* Main container with ambient glow */
        .stApp, [data-testid="stAppViewContainer"] {
            background: 
                radial-gradient(ellipse at 20% 0%, rgba(251, 191, 36, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(99, 102, 241, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(20, 184, 166, 0.04) 0%, transparent 70%),
                linear-gradient(135deg, #0C0C0E 0%, #141416 50%, #18181B 100%) !important;
        }
        
        /* Sidebar - Sleek glass morphism */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(28, 28, 31, 0.95) 0%, rgba(20, 20, 22, 0.98) 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #E2E8F0 !important;
        }
        
        /* Headings - Bright and clear */
        h1, h2, h3, h4, h5, h6 {
            color: #F8FAFC !important;
            font-weight: 700 !important;
        }
        
        /* Title with gradient */
        [data-testid="stMarkdownContainer"] h1 {
            background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 50%, #D97706 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        p, span, label {
            color: #CBD5E1 !important;
        }
        
        div {
            color: #E2E8F0 !important;
        }
        
        /* Metric cards - Glowing dark cards */
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, #1C1C1F 0%, #242428 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.3),
                0 10px 15px -3px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(251, 191, 36, 0.3) !important;
            box-shadow: 
                0 10px 20px -5px rgba(0, 0, 0, 0.4),
                0 0 30px rgba(251, 191, 36, 0.1) !important;
        }
        
        .stMetric label {
            color: #94A3B8 !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        
        .stMetric [data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
        }
        
        /* Inputs - Dark with glow on focus */
        .stTextInput input, .stTextArea textarea {
            background: #1C1C1F !important;
            color: #F8FAFC !important;
            border: 2px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            transition: all 0.2s ease !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #FBBF24 !important;
            box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.15), 0 0 20px rgba(251, 191, 36, 0.1) !important;
            outline: none !important;
        }
        
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {
            color: #64748B !important;
        }
        
        /* Buttons - Glowing gold */
        .stButton > button {
            background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%) !important;
            color: #0C0C0E !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(251, 191, 36, 0.4), 0 0 20px rgba(251, 191, 36, 0.2) !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(251, 191, 36, 0.5), 0 0 40px rgba(251, 191, 36, 0.3) !important;
        }
        
        /* Secondary/disabled buttons */
        .stButton > button[kind="secondary"],
        .stButton > button:disabled {
            background: linear-gradient(145deg, #242428 0%, #1C1C1F 100%) !important;
            color: #94A3B8 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* Dividers - Subtle glow */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, rgba(251, 191, 36, 0.3), transparent) !important;
            margin: 24px 0 !important;
        }
        
        /* Header */
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        
        /* Cards/containers */
        [data-testid="stExpander"] {
            background: #1C1C1F !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px !important;
            height: 8px !important;
        }
        
        ::-webkit-scrollbar-track {
            background: #141416 !important;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #3F3F46 !important;
            border-radius: 4px !important;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #52525B !important;
        }
        """
        st.markdown(f"<style>{dark_css}</style>", unsafe_allow_html=True)


def _apply_direction() -> None:
    """Apply text direction and language attributes to the page."""
    direction = get_direction()
    lang = get_language()
    theme = st.session_state.get("theme", "light")

    # #region agent log
    import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"H","location":"app.py:_apply_direction","message":"applying_direction_theme","data":{"direction":direction,"lang":lang,"theme":theme},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion

    st.markdown(
        f"""
        <script>
            document.documentElement.setAttribute('dir', '{direction}');
            document.documentElement.setAttribute('lang', '{lang}');
            document.documentElement.setAttribute('data-theme', '{theme}');
            // Also try to apply to stApp container
            var stApp = document.querySelector('[data-testid="stAppViewContainer"]');
            if (stApp) stApp.setAttribute('data-theme', '{theme}');
            var stAppMain = document.querySelector('[data-testid="stApp"]');
            if (stAppMain) stAppMain.setAttribute('data-theme', '{theme}');
            console.log('ARIA Theme Applied:', '{theme}');
        </script>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# State Management
# =============================================================================

def _init_state() -> None:
    """Initialize session state with defaults."""
    # #region agent log
    import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"B","location":"app.py:_init_state","message":"init_state_start","data":{"existing_keys":list(st.session_state.keys())[:10]},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion
    defaults: dict[str, Any] = {
        # Session
        "session_id": str(uuid4()),
        "started_at": datetime.now(tz=UTC),
        "status": "idle",

        # Chat
        "messages": [],

        # Events
        "events": [],

        # HITL
        "hitl_request": None,

        # Browser
        "screenshot_base64": None,
        "page_info": {},

        # Plan & Steps
        "plan": None,
        "current_step": {},

        # Settings
        "language": "en",
        "theme": "light",

        # Metrics
        "metrics": {
            "tasks_today": 0,
            "success_rate": 0,
            "hitl_rate": 0,
            "time_saved_minutes": 0,
        },
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _add_event(event_type: str, message: str) -> None:
    """Add event to activity log."""
    st.session_state.events.append({
        "time": datetime.now(tz=UTC).strftime("%H:%M:%S"),
        "type": event_type,
        "message": message,
    })


# =============================================================================
# Event Handlers
# =============================================================================

def _handle_chat(prompt: str) -> None:
    """Handle chat message submission and get LLM response."""
    import asyncio  # noqa: PLC0415

    add_message(st.session_state.messages, "user", prompt)
    _add_event("human.chat", f"User: {prompt}")

    # Show thinking indicator
    with st.spinner(t("chat.thinking")):
        try:
            # Get LLM response
            response_text = asyncio.run(_get_llm_response(prompt))
            add_message(st.session_state.messages, "assistant", response_text)
            _add_event("agent.response", f"ARIA: {response_text[:50]}...")
        except Exception as e:  # noqa: BLE001
            error_msg = f"❌ {t('chat.error')}: {e!s}"
            add_message(st.session_state.messages, "assistant", error_msg)
            _add_event("error", str(e))


async def _get_llm_response(prompt: str) -> str:
    """Get response from local LLM (Ollama)."""
    try:
        from aria.core.llm import get_llm_client  # noqa: PLC0415
        from aria.core.llm.base import Message, ModelRole  # noqa: PLC0415

        client = get_llm_client()

        # Build conversation history for context
        messages = []

        # System message for ARIA personality
        system_msg = """You are ARIA (Adaptive Reasoning & Intelligent Automation), a helpful AI assistant.
You assist users with job searching, resume building, and career advice.
Be friendly, professional, and helpful. Respond in the same language the user uses.
If user writes in Persian/Farsi, respond in Persian. If in English, respond in English."""

        messages.append(Message(role="system", content=system_msg))

        # Add recent conversation history (last 10 messages for context)
        for msg in st.session_state.messages[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content and content != t("chat.thinking"):
                messages.append(Message(role=role, content=content))

        # Add current user message
        messages.append(Message(role="user", content=prompt))

        # Detect language and use appropriate model
        is_persian = any(
            "\u0600" <= c <= "\u06ff" or "\u0750" <= c <= "\u077f" for c in prompt
        )
        role = ModelRole.BRAIN_PERSIAN if is_persian else ModelRole.BRAIN

        # Generate response
        response = await client.generate(
            messages=messages,
            role=role,
            temperature=0.7,
            max_tokens=1000,
        )

        return response.content

    except Exception as e:
        # Fallback error message
        raise RuntimeError(f"LLM connection failed: {e}") from e


def _handle_hitl(response: dict[str, Any]) -> None:
    """Handle HITL panel response."""
    st.session_state.hitl_request = None
    _add_event("human.hitl", f"HITL: {response.get('action')}")


def _handle_language_change(lang: str) -> None:
    """Handle language change."""
    set_language(lang)
    st.session_state.language = lang
    st.rerun()


def _handle_theme_change(theme: str) -> None:
    """Handle theme change."""
    # #region agent log
    import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"G","location":"app.py:_handle_theme_change","message":"theme_change_triggered","data":{"new_theme":theme,"old_theme":st.session_state.get("theme","?")},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion
    st.session_state.theme = theme
    st.rerun()


def _handle_new_session() -> None:
    """Handle new session creation."""
    st.session_state.session_id = str(uuid4())
    st.session_state.started_at = datetime.now(tz=UTC)
    st.session_state.messages = []
    st.session_state.events = []
    st.session_state.status = "idle"
    st.session_state.hitl_request = None
    st.session_state.current_step = {}
    st.session_state.plan = None
    _add_event("system", "Session reset")


# =============================================================================
# UI Components
# =============================================================================

def _render_header() -> None:
    """Render the header with title and controls."""
    col_title, col_controls = st.columns([3, 1])

    with col_title:
        st.title(t("app.title"))
        st.caption(t("app.subtitle"))

    with col_controls:
        # Language and theme controls in a row
        ctrl_col1, ctrl_col2 = st.columns(2)

        with ctrl_col1:
            # Language selector
            current_lang = get_language()
            lang_options = {"en": "EN", "fa": "فا"}
            selected_lang = st.selectbox(
                t("settings.language"),
                options=list(lang_options.keys()),
                format_func=lambda x: lang_options[x],
                index=0 if current_lang == "en" else 1,
                key="lang_selector",
                label_visibility="collapsed",
            )
            if selected_lang != current_lang:
                _handle_language_change(selected_lang)

        with ctrl_col2:
            # Theme toggle
            current_theme = st.session_state.get("theme", "light")
            theme_icon = "🌙" if current_theme == "light" else "☀️"
            # #region agent log
            import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"G","location":"app.py:theme_toggle_render","message":"theme_button_rendered","data":{"current_theme":current_theme,"icon":theme_icon},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
            # #endregion
            if st.button(theme_icon, key="theme_toggle", help=t("tooltip.theme")):
                # #region agent log
                open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"G","location":"app.py:theme_toggle_clicked","message":"theme_button_CLICKED","data":{"will_change_to":"dark" if current_theme == "light" else "light"},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
                # #endregion
                new_theme = "dark" if current_theme == "light" else "light"
                _handle_theme_change(new_theme)


def _render_metrics_row() -> None:
    """Render the metrics row at the top."""
    metrics = st.session_state.get("metrics", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            t("metrics.tasks_today"),
            metrics.get("tasks_today", 0),
            delta=None,
        )

    with col2:
        success_rate = metrics.get("success_rate", 0)
        st.metric(
            t("metrics.success_rate"),
            f"{success_rate}%",
            delta=None,
        )

    with col3:
        hitl_rate = metrics.get("hitl_rate", 0)
        st.metric(
            t("metrics.hitl_rate"),
            f"{hitl_rate}%",
            delta=None,
        )

    with col4:
        time_saved = metrics.get("time_saved_minutes", 0)
        st.metric(
            t("metrics.time_saved"),
            f"{time_saved}m",
            delta=None,
        )


def _handle_start(goal: str) -> None:
    """Handle task start."""
    st.session_state.status = "running"
    st.session_state.current_goal = goal
    _add_event("brain.start", f"Task started: {goal}")
    add_message(st.session_state.messages, "user", goal)
    add_message(
        st.session_state.messages,
        "assistant",
        f"🚀 {t('status.running')}: {goal}",
    )


def _handle_pause() -> None:
    """Handle task pause."""
    st.session_state.status = "paused"
    _add_event("brain.pause", "Task paused")


def _handle_resume() -> None:
    """Handle task resume."""
    st.session_state.status = "running"
    _add_event("brain.resume", "Task resumed")


def _handle_stop() -> None:
    """Handle task stop."""
    st.session_state.status = "idle"
    _add_event("brain.stop", "Task stopped")


def _handle_browser_action(action: str | tuple[str, str] | None) -> None:
    """Handle browser control actions.

    Args:
        action: Action string or (action, value) tuple

    """
    if not action:
        return

    try:
        from aria.ui.hooks.use_websocket import send_ws_message  # noqa: PLC0415

        if isinstance(action, tuple):
            cmd, value = action
            send_ws_message({
                "type": "browser_action",
                "action": cmd,
                "value": value,
            })
        else:
            send_ws_message({
                "type": "browser_action",
                "action": action,
            })

    except Exception:  # noqa: BLE001, S110
        pass  # Silently ignore - WebSocket may not be available


def _render_sidebar() -> None:
    """Render the sidebar with navigation and quick actions."""
    with st.sidebar:
        # Logo/Brand
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="margin: 0;">🤖 ARIA</h2>
                <p style="color: var(--color-text-muted); font-size: 0.875rem;">
                    {t("app.description")}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Goal Input (when idle)
        status = st.session_state.get("status", "idle")
        if status in ("idle", "completed", "failed"):
            st.subheader(f"🎯 {t('chat.placeholder')}")
            goal = render_goal_input()
            if goal:
                _handle_start(goal)
                st.rerun()

            st.divider()

        # Agent Controls (compact mode for sidebar)
        st.subheader(f"🎮 {t('dashboard.quick_actions')}")

        action = render_agent_controls(
            status=status,
            on_start=lambda: None,  # Handled by goal input
            on_pause=_handle_pause,
            on_resume=_handle_resume,
            on_stop=_handle_stop,
            compact=True,  # Use compact layout for sidebar
        )
        if action in ("pause", "resume", "stop"):
            st.rerun()

        st.divider()

        # Quick Actions
        if st.button(
            f"🆕 {t('controls.new_session')}",
            key="btn_new_session",
            use_container_width=True,
        ):
            _handle_new_session()
            st.rerun()

        # Simulate HITL (for testing)
        if st.button(
            f"🧪 {t('hitl.title')} (Test)",
            key="btn_test_hitl",
            use_container_width=True,
        ):
            st.session_state.hitl_request = {
                "reason": "confirmation",
                "context": {"action": "Submit application"},
            }
            _add_event("brain.hitl", "HITL requested (test)")
            st.rerun()

        st.divider()

        # Status
        st.subheader(t("dashboard.system_health"))

        status_color = {
            "idle": "gray",
            "running": "green",
            "paused": "orange",
            "waiting_human": "blue",
            "completed": "green",
            "failed": "red",
        }.get(status, "gray")

        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem;
                background: var(--color-bg-secondary);
                border-radius: var(--radius-md);
            ">
                <span style="
                    width: 10px;
                    height: 10px;
                    background: {status_color};
                    border-radius: 50%;
                    display: inline-block;
                "></span>
                <span>{t(f'status.{status}')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Session info
        st.caption(f"{t('session.id')}: {st.session_state.session_id[:8]}...")
        st.caption(f"{t('session.domain')}: job_apply")
        if st.session_state.get("current_goal"):
            st.caption(f"🎯 {st.session_state.current_goal[:30]}...")


# =============================================================================
# Model Warmup
# =============================================================================

def _warmup_models() -> None:
    """Warmup LLM models on first load to eliminate cold start."""
    # Only warmup once per session
    if st.session_state.get("_models_warmed_up"):
        return

    # Show warmup status in sidebar
    if not st.session_state.get("_warmup_started"):
        st.session_state._warmup_started = True
        
        # Start warmup in background (non-blocking)
        import threading  # noqa: PLC0415

        def _do_warmup() -> None:
            try:
                import httpx  # noqa: PLC0415

                # Warmup primary chat model
                with httpx.Client(timeout=120.0) as client:
                    client.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "aria-persian-chat",
                            "prompt": "سلام",
                            "stream": False,
                            "options": {"num_predict": 1},
                            "keep_alive": -1,
                        },
                    )
                st.session_state._models_warmed_up = True
            except Exception:  # noqa: BLE001, S110
                pass  # Silently fail if Ollama not running

        # Run warmup in background thread
        thread = threading.Thread(target=_do_warmup, daemon=True)
        thread.start()


# =============================================================================
# Auto-refresh & Data Fetching
# =============================================================================

def _fetch_updates() -> None:  # noqa: C901
    """Fetch updates from backend API or WebSocket silently."""
    # Track backend availability to avoid repeated calls
    backend_key = "_backend_available"
    check_interval = 30  # Check every 30 seconds if backend was unavailable
    last_check = st.session_state.get("_last_backend_check", 0)
    backend_available = st.session_state.get(backend_key, True)

    # Skip if backend was recently unavailable
    if not backend_available and (time.time() - last_check) < check_interval:
        return

    # Try WebSocket first for real-time updates
    try:
        from aria.ui.hooks.use_websocket import (  # noqa: PLC0415
            connect_websocket,
            handle_ws_message,
        )

        message = connect_websocket(
            session_id=st.session_state.get("session_id"),
            key="main_ws",
        )

        if message:
            handle_ws_message(message)
            st.session_state[backend_key] = True
            return  # WebSocket update is sufficient
    except Exception:  # noqa: BLE001, S110
        pass

    # Fallback to REST API polling
    try:
        from aria.ui.services.api_client import APIClient  # noqa: PLC0415

        client = APIClient()

        # Check if backend is available
        health = client.health_check()
        st.session_state["_last_backend_check"] = time.time()

        if health.get("status") == "unhealthy":
            st.session_state[backend_key] = False
            return

        st.session_state[backend_key] = True

        # Fetch task status if we have a session
        if st.session_state.get("task_id"):
            task = client.get_task(st.session_state.task_id)
            if task and not task.get("error"):
                st.session_state.status = task.get("status", "idle")

                # Update current step if available
                if task.get("current_step"):
                    st.session_state.current_step = task["current_step"]

                # Check for HITL request
                if task.get("hitl_request"):
                    st.session_state.hitl_request = task["hitl_request"]

                # Update screenshot if available
                if task.get("screenshot"):
                    st.session_state.screenshot_base64 = task["screenshot"]
                    st.session_state.page_info = task.get("page_info", {})

        # Fetch metrics
        metrics = client.get_metrics()
        if not metrics.get("error"):
            st.session_state.metrics = {
                "tasks_today": metrics.get("tasks_today", 0),
                "success_rate": metrics.get("success_rate", 0),
                "hitl_rate": metrics.get("hitl_rate", 0),
                "time_saved_minutes": metrics.get("time_saved_minutes", 0),
            }

    except Exception as _exc:  # noqa: BLE001
        # Silently ignore errors - backend may not be running
        # #region agent log
        import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"E","location":"app.py:_fetch_updates","message":"api_error","data":{"error":str(_exc)[:100]},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        st.session_state[backend_key] = False
        st.session_state["_last_backend_check"] = time.time()


def _should_auto_refresh() -> bool:
    """Check if auto-refresh should be enabled."""
    status = st.session_state.get("status", "idle")
    return status in AUTO_REFRESH_ENABLED_STATUSES


def _setup_auto_refresh() -> None:
    """Set up auto-refresh using streamlit-autorefresh or fallback."""
    if not _should_auto_refresh():
        return

    try:
        # Try to use streamlit-autorefresh if available
        from streamlit_autorefresh import st_autorefresh  # noqa: PLC0415

        st_autorefresh(
            interval=AUTO_REFRESH_INTERVAL * 1000,
            limit=None,
            key="auto_refresh",
        )
    except ImportError:
        # Fallback: manual refresh indicator
        st.sidebar.info(
            f"🔄 Auto-refresh every {AUTO_REFRESH_INTERVAL}s (Status: Running)",
        )

        # Store last refresh time
        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = time.time()

        # Check if enough time has passed
        elapsed = time.time() - st.session_state.last_refresh
        if elapsed >= AUTO_REFRESH_INTERVAL:
            st.session_state.last_refresh = time.time()
            _fetch_updates()
            st.rerun()


# =============================================================================
# Main Application
# =============================================================================

def main() -> None:
    """Run the main application entry point."""
    # #region agent log
    import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"A","location":"app.py:main","message":"main_start","data":{},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion
    # Page configuration
    st.set_page_config(
        page_title="ARIA Control Room",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize state
    _init_state()

    # Warmup LLM models (only once on first load)
    _warmup_models()

    # Fetch updates from backend
    _fetch_updates()

    # Load styles
    _load_styles()
    _apply_direction()

    # Get settings
    settings = get_settings().ui

    # Render header
    _render_header()

    # Metrics row
    _render_metrics_row()

    st.divider()

    # Main layout: 2 columns
    col_main, col_side = st.columns([2, 1], gap="large")

    with col_main:
        # Browser View
        if settings.features.live_browser_view:
            render_browser_view(
                st.session_state.screenshot_base64,
                st.session_state.page_info,
                auto_refresh=_should_auto_refresh(),
            )
            action = render_browser_controls()
            if action:
                _add_event("hand.browser", f"Browser: {action}")
                _handle_browser_action(action)

        # HITL Panel (conditionally shown)
        if settings.features.hitl_panel and st.session_state.hitl_request:
            st.divider()
            response = render_hitl_panel(st.session_state.hitl_request)
            if response:
                _handle_hitl(response)

        # Chat Interface
        if settings.features.chat_interface:
            st.divider()
            render_chat(
                st.session_state.messages,
                on_send=_handle_chat,
            )

    with col_side:
        # Current Step / Plan
        render_step_panel(st.session_state.current_step)

        st.divider()

        # Activity Log
        if settings.features.activity_log:
            render_activity_log(st.session_state.events)

    # Sidebar
    _render_sidebar()

    # Status Bar (bottom)
    st.divider()
    render_status_bar(
        status=st.session_state.status,
        domain="job_apply",
        session_id=st.session_state.session_id,
        started_at=st.session_state.started_at,
    )

    # Setup auto-refresh for running tasks
    _setup_auto_refresh()
    # #region agent log
    import json; open(r'd:\Projects\WorkFinder\.cursor\debug.log','a').write(json.dumps({"hypothesisId":"A","location":"app.py:main","message":"main_complete","data":{"status":st.session_state.get("status","?"),"session":st.session_state.get("session_id","?")[:8]},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session"})+'\n')
    # #endregion


if __name__ == "__main__":
    main()
