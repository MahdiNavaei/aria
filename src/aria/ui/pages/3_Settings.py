"""Settings page - Application configuration and preferences."""

from __future__ import annotations

import streamlit as st

from aria.config import get_settings
from aria.ui.i18n import get_available_languages, get_language, set_language, t


def main() -> None:
    """Render the settings page."""
    st.title(t("settings.title"))
    st.caption(t("settings.subtitle"))

    # Settings sections
    tab_general, tab_automation, tab_advanced = st.tabs([
        "⚙️ General",
        f"🤖 {t('settings.automation')}",
        f"🔧 {t('settings.advanced')}",
    ])

    with tab_general:
        st.subheader(t("settings.language"))

        # Language selection
        languages = get_available_languages()
        current_lang = get_language()

        lang_col1, lang_col2 = st.columns([1, 2])

        with lang_col1:
            selected_lang = st.selectbox(
                t("settings.language"),
                options=[lang["code"] for lang in languages],
                format_func=lambda x: next(
                    (lang["native_name"] for lang in languages if lang["code"] == x),
                    x,
                ),
                index=0 if current_lang == "en" else 1,
                key="settings_language",
                label_visibility="collapsed",
            )

            if selected_lang != current_lang:
                set_language(selected_lang)
                st.session_state.language = selected_lang
                st.rerun()

        with lang_col2:
            st.info(
                "🌐 Changing the language will update all UI text. "
                "Persian (فارسی) enables RTL layout.",
            )

        st.divider()

        st.subheader(t("settings.theme"))

        theme_col1, theme_col2 = st.columns([1, 2])

        with theme_col1:
            current_theme = st.session_state.get("theme", "light")
            theme_options = {
                "light": t("settings.theme.light"),
                "dark": t("settings.theme.dark"),
                "auto": t("settings.theme.auto"),
            }

            selected_theme = st.selectbox(
                t("settings.theme"),
                options=list(theme_options.keys()),
                format_func=lambda x: theme_options[x],
                index=list(theme_options.keys()).index(current_theme),
                key="settings_theme",
                label_visibility="collapsed",
            )

            if selected_theme != current_theme:
                st.session_state.theme = selected_theme
                st.rerun()

        with theme_col2:
            st.info(
                "🎨 Choose your preferred color theme. "
                "Dark mode is easier on the eyes in low light.",
            )

        st.divider()

        st.subheader(t("settings.notifications"))

        notif_col1, notif_col2 = st.columns(2)

        with notif_col1:
            st.checkbox(
                f"🔔 {t('settings.notifications.sound')}",
                value=True,
                key="settings_sound",
            )

        with notif_col2:
            st.checkbox(
                f"💻 {t('settings.notifications.desktop')}",
                value=False,
                key="settings_desktop",
            )

    with tab_automation:
        st.subheader(t("settings.automation"))

        st.checkbox(
            f"🚀 {t('settings.automation.auto_apply')}",
            value=False,
            key="settings_auto_apply",
            help="When enabled, ARIA will automatically submit applications to high-match jobs.",
        )

        st.checkbox(
            f"✅ {t('settings.automation.require_approval')}",
            value=True,
            key="settings_require_approval",
            help="Require your confirmation before submitting any application.",
        )

        st.divider()

        st.subheader("Match Threshold")

        match_threshold = st.slider(
            "Minimum match score for auto-apply",
            min_value=50,
            max_value=100,
            value=80,
            step=5,
            key="settings_match_threshold",
            format="%d%%",
        )

        st.caption(f"Jobs with match score below {match_threshold}% will be skipped.")

        st.divider()

        st.subheader("Job Sources")

        source_col1, source_col2 = st.columns(2)

        with source_col1:
            st.checkbox("🔗 LinkedIn", value=True, key="source_linkedin")
            st.checkbox("🔗 Indeed", value=True, key="source_indeed")

        with source_col2:
            st.checkbox("🔗 Glassdoor", value=False, key="source_glassdoor")
            st.checkbox("🔗 Company Sites", value=True, key="source_company")

    with tab_advanced:
        st.subheader(t("settings.advanced"))

        st.checkbox(
            f"🐛 {t('settings.advanced.debug')}",
            value=False,
            key="settings_debug",
            help="Enable debug mode for detailed logging.",
        )

        st.divider()

        st.subheader("Current Configuration")

        try:
            settings = get_settings()

            with st.expander("🔧 UI Settings", expanded=False):
                st.json(settings.ui.model_dump())

            with st.expander("🌐 API Settings", expanded=False):
                st.json(settings.api.model_dump())

            with st.expander("🎤 Voice Settings", expanded=False):
                st.json(settings.voice.model_dump())

        except Exception as exc:  # noqa: BLE001
            st.warning(f"Could not load settings: {exc}")

        st.divider()

        st.subheader("Data Management")

        export_col, import_col, reset_col = st.columns(3)

        with export_col:
            if st.button(
                f"📤 {t('settings.advanced.export')}",
                use_container_width=True,
            ):
                st.toast("Exporting settings...", icon="📤")

        with import_col:
            if st.button(
                f"📥 {t('settings.advanced.import')}",
                use_container_width=True,
            ):
                st.toast("Import feature coming soon!", icon="📥")

        with reset_col:
            if st.button(
                f"🔄 {t('settings.advanced.reset')}",
                use_container_width=True,
                type="secondary",
            ):
                st.toast("Reset feature coming soon!", icon="🔄")

    st.divider()

    # Save button
    if st.button(
        f"💾 {t('settings.save')}",
        type="primary",
        use_container_width=True,
    ):
        st.success(f"✅ {t('settings.saved')}")


if __name__ == "__main__":
    main()
