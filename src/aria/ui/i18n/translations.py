"""Translation strings for ARIA UI - Persian (FA) and English (EN)."""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # ============================================================
        # Application
        # ============================================================
        "app.title": "ARIA Control Room",
        "app.subtitle": "Adaptive Reasoning & Intelligent Automation",
        "app.description": "Your AI assistant for intelligent task automation",

        # ============================================================
        # Navigation
        # ============================================================
        "nav.dashboard": "Dashboard",
        "nav.jobs": "Jobs",
        "nav.analytics": "Analytics",
        "nav.settings": "Settings",
        "nav.help": "Help",
        "nav.logout": "Logout",

        # ============================================================
        # Status
        # ============================================================
        "status.idle": "Idle",
        "status.running": "Running",
        "status.paused": "Paused",
        "status.waiting_human": "Waiting for Human",
        "status.completed": "Completed",
        "status.failed": "Failed",
        "status.cancelled": "Cancelled",
        "status.connecting": "Connecting...",
        "status.reconnecting": "Reconnecting...",
        "status.disconnected": "Disconnected",

        # ============================================================
        # Human-in-the-Loop (HITL)
        # ============================================================
        "hitl.title": "Human Input Required",
        "hitl.subtitle": "ARIA needs your help to continue",
        "hitl.reason.captcha": "CAPTCHA detected. Please solve it in the browser window.",
        "hitl.reason.login": "Login required. Please sign in to continue.",
        "hitl.reason.confirmation": "This action requires your confirmation before proceeding.",
        "hitl.reason.error": "An error occurred that needs your attention.",
        "hitl.reason.unknown": "ARIA needs your input to continue.",
        "hitl.action.approve": "Approve",
        "hitl.action.reject": "Reject",
        "hitl.action.completed": "I've Done It",
        "hitl.action.retry": "Retry",
        "hitl.action.skip": "Skip",
        "hitl.action.abort": "Abort Task",
        "hitl.reject_reason": "Reason for rejection",
        "hitl.reject_reason_placeholder": "Optional: Why are you rejecting?",

        # ============================================================
        # Chat Interface
        # ============================================================
        "chat.title": "Chat",
        "chat.placeholder": "Type a goal or command...",
        "chat.placeholder_voice": "Tap to speak...",
        "chat.voice_button": "Voice Input",
        "chat.voice_listening": "Listening...",
        "chat.voice_processing": "Processing...",
        "chat.send": "Send",
        "chat.clear": "Clear Chat",
        "chat.export": "Export",
        "chat.thinking": "ARIA is thinking...",
        "chat.error": "Connection error",
        "chat.welcome": "Hello! I'm ARIA, your intelligent automation assistant. How can I help you today?",
        "chat.welcome_hint": 'Try saying: "Find Python developer jobs on LinkedIn"',

        # ============================================================
        # Browser View
        # ============================================================
        "browser.title": "Live Browser View",
        "browser.no_view": "No browser view available",
        "browser.no_view_hint": "Start a task to see live browser updates",
        "browser.loading": "Loading browser view...",
        "browser.refresh": "Refresh",
        "browser.back": "Back",
        "browser.forward": "Forward",
        "browser.url_placeholder": "Enter URL...",
        "browser.navigate": "Go",
        "browser.take_control": "Take Control",
        "browser.release_control": "Release Control",
        "browser.fullscreen": "Fullscreen",
        "browser.screenshot": "Screenshot",

        # ============================================================
        # Activity Log
        # ============================================================
        "log.title": "Activity Log",
        "log.filter": "Filter",
        "log.filter.all": "All",
        "log.filter.brain": "Brain",
        "log.filter.hand": "Hand",
        "log.filter.eye": "Eye",
        "log.filter.human": "Human",
        "log.filter.error": "Errors",
        "log.search": "Search...",
        "log.clear": "Clear Log",
        "log.export": "Export Log",
        "log.empty": "No activity yet",
        "log.empty_hint": "Events will appear here as ARIA works",

        # ============================================================
        # Step Panel
        # ============================================================
        "step.title": "Current Step",
        "step.no_step": "No active step",
        "step.no_step_hint": "Start a task to see progress",
        "step.of": "of",
        "step.progress": "Progress",
        "step.confidence": "Confidence",
        "step.elapsed": "Elapsed",
        "step.estimated": "Est. remaining",

        # ============================================================
        # Plan View
        # ============================================================
        "plan.title": "Execution Plan",
        "plan.no_plan": "No plan yet",
        "plan.step_pending": "Pending",
        "plan.step_running": "Running",
        "plan.step_completed": "Completed",
        "plan.step_failed": "Failed",
        "plan.step_skipped": "Skipped",
        "plan.edit": "Edit Plan",
        "plan.approve": "Approve Plan",
        "plan.regenerate": "Regenerate",

        # ============================================================
        # Controls
        # ============================================================
        "controls.start": "Start",
        "controls.pause": "Pause",
        "controls.resume": "Resume",
        "controls.stop": "Stop",
        "controls.restart": "Restart",
        "controls.new_session": "New Session",

        # ============================================================
        # Metrics
        # ============================================================
        "metrics.tasks_today": "Tasks Today",
        "metrics.success_rate": "Success Rate",
        "metrics.hitl_rate": "HITL Rate",
        "metrics.time_saved": "Time Saved",
        "metrics.jobs_applied": "Jobs Applied",
        "metrics.skills_learned": "Skills Learned",
        "metrics.policies_active": "Active Policies",

        # ============================================================
        # Dashboard
        # ============================================================
        "dashboard.title": "Dashboard",
        "dashboard.subtitle": "Overview of recent activity and system health",
        "dashboard.recent_tasks": "Recent Tasks",
        "dashboard.quick_actions": "Quick Actions",
        "dashboard.system_health": "System Health",
        "dashboard.learning_progress": "Learning Progress",

        # ============================================================
        # Jobs Page
        # ============================================================
        "jobs.title": "Jobs",
        "jobs.subtitle": "Manage your job applications",
        "jobs.search": "Search jobs...",
        "jobs.filter_status": "Filter by status",
        "jobs.status.all": "All",
        "jobs.status.new": "New",
        "jobs.status.matched": "Matched",
        "jobs.status.applied": "Applied",
        "jobs.status.rejected": "Rejected",
        "jobs.status.interview": "Interview",
        "jobs.no_jobs": "No jobs found",
        "jobs.no_jobs_hint": "Start applying to see jobs here",
        "jobs.add_url": "Add Job URL",
        "jobs.refresh": "Refresh",

        # ============================================================
        # Analytics Page
        # ============================================================
        "analytics.title": "Analytics",
        "analytics.subtitle": "Learning and execution metrics",
        "analytics.period": "Period",
        "analytics.period.today": "Today",
        "analytics.period.week": "This Week",
        "analytics.period.month": "This Month",
        "analytics.period.all": "All Time",
        "analytics.chart.applications": "Applications Over Time",
        "analytics.chart.success": "Success Rate Trend",
        "analytics.chart.skills": "Skills Distribution",

        # ============================================================
        # Settings Page
        # ============================================================
        "settings.title": "Settings",
        "settings.subtitle": "Configure ARIA to your preferences",
        "settings.language": "Language",
        "settings.language.en": "English",
        "settings.language.fa": "فارسی (Persian)",
        "settings.theme": "Theme",
        "settings.theme.light": "Light",
        "settings.theme.dark": "Dark",
        "settings.theme.auto": "Auto (System)",
        "settings.notifications": "Notifications",
        "settings.notifications.sound": "Sound alerts",
        "settings.notifications.desktop": "Desktop notifications",
        "settings.automation": "Automation",
        "settings.automation.auto_apply": "Auto-apply to matched jobs",
        "settings.automation.require_approval": "Require approval for submissions",
        "settings.advanced": "Advanced",
        "settings.advanced.debug": "Debug mode",
        "settings.advanced.export": "Export settings",
        "settings.advanced.import": "Import settings",
        "settings.advanced.reset": "Reset to defaults",
        "settings.save": "Save Settings",
        "settings.saved": "Settings saved!",

        # ============================================================
        # Session Info
        # ============================================================
        "session.id": "Session",
        "session.domain": "Domain",
        "session.elapsed": "Elapsed",
        "session.started": "Started",

        # ============================================================
        # Errors & Messages
        # ============================================================
        "error.generic": "An error occurred",
        "error.connection": "Connection lost. Attempting to reconnect...",
        "error.timeout": "Request timed out",
        "error.not_found": "Not found",
        "error.permission": "Permission denied",
        "success.generic": "Operation completed successfully",
        "warning.unsaved": "You have unsaved changes",
        "confirm.delete": "Are you sure you want to delete this?",
        "confirm.stop": "Are you sure you want to stop the current task?",

        # ============================================================
        # Tooltips & Help
        # ============================================================
        "tooltip.language": "Switch language",
        "tooltip.theme": "Toggle theme",
        "tooltip.fullscreen": "Toggle fullscreen",
        "tooltip.settings": "Open settings",
        "tooltip.help": "Get help",
        "help.keyboard": "Keyboard Shortcuts",
        "help.keyboard.pause": "Pause/Resume",
        "help.keyboard.stop": "Stop task",
        "help.keyboard.voice": "Voice input",
        "help.keyboard.fullscreen": "Fullscreen",
    },

    "fa": {
        # ============================================================
        # Application
        # ============================================================
        "app.title": "اتاق کنترل ARIA",
        "app.subtitle": "استدلال تطبیقی و اتوماسیون هوشمند",
        "app.description": "دستیار هوشمند شما برای اتوماسیون وظایف",

        # ============================================================
        # Navigation
        # ============================================================
        "nav.dashboard": "داشبورد",
        "nav.jobs": "شغل‌ها",
        "nav.analytics": "آمار و تحلیل",
        "nav.settings": "تنظیمات",
        "nav.help": "راهنما",
        "nav.logout": "خروج",

        # ============================================================
        # Status
        # ============================================================
        "status.idle": "آماده",
        "status.running": "در حال اجرا",
        "status.paused": "متوقف",
        "status.waiting_human": "منتظر تأیید انسان",
        "status.completed": "تکمیل شده",
        "status.failed": "ناموفق",
        "status.cancelled": "لغو شده",
        "status.connecting": "در حال اتصال...",
        "status.reconnecting": "اتصال مجدد...",
        "status.disconnected": "قطع شده",

        # ============================================================
        # Human-in-the-Loop (HITL)
        # ============================================================
        "hitl.title": "نیاز به ورودی انسان",
        "hitl.subtitle": "ARIA برای ادامه به کمک شما نیاز دارد",
        "hitl.reason.captcha": "کپچا شناسایی شد. لطفاً آن را در پنجره مرورگر حل کنید.",
        "hitl.reason.login": "ورود به سیستم لازم است. لطفاً وارد شوید.",
        "hitl.reason.confirmation": "این اقدام نیاز به تأیید شما قبل از اجرا دارد.",
        "hitl.reason.error": "خطایی رخ داده که نیاز به توجه شما دارد.",
        "hitl.reason.unknown": "ARIA برای ادامه به ورودی شما نیاز دارد.",
        "hitl.action.approve": "تأیید",
        "hitl.action.reject": "رد",
        "hitl.action.completed": "انجام دادم",
        "hitl.action.retry": "تلاش مجدد",
        "hitl.action.skip": "رد شدن",
        "hitl.action.abort": "لغو کار",
        "hitl.reject_reason": "دلیل رد",
        "hitl.reject_reason_placeholder": "اختیاری: چرا رد می‌کنید؟",

        # ============================================================
        # Chat Interface
        # ============================================================
        "chat.title": "گفتگو",
        "chat.placeholder": "هدف یا دستور خود را بنویسید...",
        "chat.placeholder_voice": "برای صحبت ضربه بزنید...",
        "chat.voice_button": "ورودی صوتی",
        "chat.voice_listening": "در حال گوش دادن...",
        "chat.voice_processing": "در حال پردازش...",
        "chat.send": "ارسال",
        "chat.clear": "پاک کردن گفتگو",
        "chat.export": "خروجی",
        "chat.thinking": "ARIA در حال فکر کردن است...",
        "chat.error": "خطا در اتصال",
        "chat.welcome": "سلام! من ARIA هستم، دستیار اتوماسیون هوشمند شما. چگونه می‌توانم کمکتان کنم؟",
        "chat.welcome_hint": "امتحان کنید: «شغل‌های برنامه‌نویس پایتون را در لینکدین پیدا کن»",

        # ============================================================
        # Browser View
        # ============================================================
        "browser.title": "نمای زنده مرورگر",
        "browser.no_view": "نمای مرورگر در دسترس نیست",
        "browser.no_view_hint": "برای دیدن به‌روزرسانی‌های زنده، یک کار شروع کنید",
        "browser.loading": "در حال بارگذاری نمای مرورگر...",
        "browser.refresh": "بارگذاری مجدد",
        "browser.back": "عقب",
        "browser.forward": "جلو",
        "browser.url_placeholder": "آدرس را وارد کنید...",
        "browser.navigate": "برو",
        "browser.take_control": "کنترل را بگیر",
        "browser.release_control": "کنترل را رها کن",
        "browser.fullscreen": "تمام صفحه",
        "browser.screenshot": "عکس صفحه",

        # ============================================================
        # Activity Log
        # ============================================================
        "log.title": "گزارش فعالیت",
        "log.filter": "فیلتر",
        "log.filter.all": "همه",
        "log.filter.brain": "مغز",
        "log.filter.hand": "دست",
        "log.filter.eye": "چشم",
        "log.filter.human": "انسان",
        "log.filter.error": "خطاها",
        "log.search": "جستجو...",
        "log.clear": "پاک کردن گزارش",
        "log.export": "خروجی گزارش",
        "log.empty": "هنوز فعالیتی نیست",
        "log.empty_hint": "رویدادها همانطور که ARIA کار می‌کند اینجا ظاهر می‌شوند",

        # ============================================================
        # Step Panel
        # ============================================================
        "step.title": "مرحله فعلی",
        "step.no_step": "مرحله فعالی نیست",
        "step.no_step_hint": "برای دیدن پیشرفت، یک کار شروع کنید",
        "step.of": "از",
        "step.progress": "پیشرفت",
        "step.confidence": "اطمینان",
        "step.elapsed": "سپری شده",
        "step.estimated": "تخمین باقی‌مانده",

        # ============================================================
        # Plan View
        # ============================================================
        "plan.title": "برنامه اجرا",
        "plan.no_plan": "هنوز برنامه‌ای نیست",
        "plan.step_pending": "در انتظار",
        "plan.step_running": "در حال اجرا",
        "plan.step_completed": "تکمیل شده",
        "plan.step_failed": "ناموفق",
        "plan.step_skipped": "رد شده",
        "plan.edit": "ویرایش برنامه",
        "plan.approve": "تأیید برنامه",
        "plan.regenerate": "ایجاد مجدد",

        # ============================================================
        # Controls
        # ============================================================
        "controls.start": "شروع",
        "controls.pause": "توقف",
        "controls.resume": "ادامه",
        "controls.stop": "پایان",
        "controls.restart": "شروع مجدد",
        "controls.new_session": "جلسه جدید",

        # ============================================================
        # Metrics
        # ============================================================
        "metrics.tasks_today": "کارهای امروز",
        "metrics.success_rate": "نرخ موفقیت",
        "metrics.hitl_rate": "نرخ دخالت انسان",
        "metrics.time_saved": "زمان صرفه‌جویی شده",
        "metrics.jobs_applied": "شغل‌های اپلای‌شده",
        "metrics.skills_learned": "مهارت‌های آموخته",
        "metrics.policies_active": "سیاست‌های فعال",

        # ============================================================
        # Dashboard
        # ============================================================
        "dashboard.title": "داشبورد",
        "dashboard.subtitle": "نمای کلی فعالیت اخیر و سلامت سیستم",
        "dashboard.recent_tasks": "کارهای اخیر",
        "dashboard.quick_actions": "اقدامات سریع",
        "dashboard.system_health": "سلامت سیستم",
        "dashboard.learning_progress": "پیشرفت یادگیری",

        # ============================================================
        # Jobs Page
        # ============================================================
        "jobs.title": "شغل‌ها",
        "jobs.subtitle": "مدیریت درخواست‌های شغلی",
        "jobs.search": "جستجوی شغل‌ها...",
        "jobs.filter_status": "فیلتر بر اساس وضعیت",
        "jobs.status.all": "همه",
        "jobs.status.new": "جدید",
        "jobs.status.matched": "تطبیق‌یافته",
        "jobs.status.applied": "اپلای‌شده",
        "jobs.status.rejected": "رد شده",
        "jobs.status.interview": "مصاحبه",
        "jobs.no_jobs": "شغلی یافت نشد",
        "jobs.no_jobs_hint": "برای دیدن شغل‌ها شروع به اپلای کنید",
        "jobs.add_url": "افزودن آدرس شغل",
        "jobs.refresh": "بارگذاری مجدد",

        # ============================================================
        # Analytics Page
        # ============================================================
        "analytics.title": "آمار و تحلیل",
        "analytics.subtitle": "آمار یادگیری و اجرا",
        "analytics.period": "دوره",
        "analytics.period.today": "امروز",
        "analytics.period.week": "این هفته",
        "analytics.period.month": "این ماه",
        "analytics.period.all": "همه زمان‌ها",
        "analytics.chart.applications": "درخواست‌ها در طول زمان",
        "analytics.chart.success": "روند نرخ موفقیت",
        "analytics.chart.skills": "توزیع مهارت‌ها",

        # ============================================================
        # Settings Page
        # ============================================================
        "settings.title": "تنظیمات",
        "settings.subtitle": "ARIA را مطابق ترجیحات خود پیکربندی کنید",
        "settings.language": "زبان",
        "settings.language.en": "English (انگلیسی)",
        "settings.language.fa": "فارسی",
        "settings.theme": "پوسته",
        "settings.theme.light": "روشن",
        "settings.theme.dark": "تاریک",
        "settings.theme.auto": "خودکار (سیستم)",
        "settings.notifications": "اعلان‌ها",
        "settings.notifications.sound": "هشدارهای صوتی",
        "settings.notifications.desktop": "اعلان‌های دسکتاپ",
        "settings.automation": "اتوماسیون",
        "settings.automation.auto_apply": "اپلای خودکار به شغل‌های مطابق",
        "settings.automation.require_approval": "نیاز به تأیید برای ارسال‌ها",
        "settings.advanced": "پیشرفته",
        "settings.advanced.debug": "حالت اشکال‌زدایی",
        "settings.advanced.export": "خروجی تنظیمات",
        "settings.advanced.import": "ورود تنظیمات",
        "settings.advanced.reset": "بازنشانی به پیش‌فرض",
        "settings.save": "ذخیره تنظیمات",
        "settings.saved": "تنظیمات ذخیره شد!",

        # ============================================================
        # Session Info
        # ============================================================
        "session.id": "نشست",
        "session.domain": "دامنه",
        "session.elapsed": "سپری شده",
        "session.started": "شروع شده",

        # ============================================================
        # Errors & Messages
        # ============================================================
        "error.generic": "خطایی رخ داد",
        "error.connection": "اتصال قطع شد. در حال تلاش برای اتصال مجدد...",
        "error.timeout": "درخواست منقضی شد",
        "error.not_found": "یافت نشد",
        "error.permission": "دسترسی رد شد",
        "success.generic": "عملیات با موفقیت انجام شد",
        "warning.unsaved": "تغییرات ذخیره‌نشده دارید",
        "confirm.delete": "آیا مطمئن هستید که می‌خواهید این را حذف کنید؟",
        "confirm.stop": "آیا مطمئن هستید که می‌خواهید کار فعلی را متوقف کنید؟",

        # ============================================================
        # Tooltips & Help
        # ============================================================
        "tooltip.language": "تغییر زبان",
        "tooltip.theme": "تغییر پوسته",
        "tooltip.fullscreen": "تغییر تمام صفحه",
        "tooltip.settings": "باز کردن تنظیمات",
        "tooltip.help": "دریافت راهنما",
        "help.keyboard": "میانبرهای صفحه‌کلید",
        "help.keyboard.pause": "توقف/ادامه",
        "help.keyboard.stop": "توقف کار",
        "help.keyboard.voice": "ورودی صوتی",
        "help.keyboard.fullscreen": "تمام صفحه",
    },
}
