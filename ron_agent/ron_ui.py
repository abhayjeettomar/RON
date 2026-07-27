import os
import sys
import tkinter as tk
# pyrefly: ignore [missing-import]
import customtkinter as ctk
from typing import Callable
import datetime

# Import local packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ron_agent.ron_engine import RonEngine
from ron_agent.voice_manager import VoiceManager

# Setup theme and design system
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Color Palette ──────────────────────────────────────────────────
BG_DARK       = "#06080F"
BG_SIDEBAR    = "#0A0E1A"
BG_SIDEBAR_HL = "#0F1328"
BG_CARD       = "#111827"
BG_INPUT      = "#0D1117"
BORDER_DIM    = "#1E293B"
BORDER_ACCENT = "#4F46E5"
ACCENT        = "#6366F1"
ACCENT_HOVER  = "#4F46E5"
ACCENT_GLOW   = "#818CF8"
SUCCESS       = "#10B981"
DANGER        = "#EF4444"
WARNING       = "#F59E0B"
TEXT_PRIMARY  = "#F1F5F9"
TEXT_SECONDARY= "#94A3B8"
TEXT_DIM      = "#475569"
USER_BUBBLE   = "#4338CA"
RON_BUBBLE    = "#1E293B"
CONSOLE_BG    = "#030712"


class RonApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ── Window Setup ──────────────────────────────────────────
        self.title("RON — AI Desktop Agent")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=BG_DARK)
        
        self.after(200, lambda: self.state("zoomed"))
        self.bind("<F11>", self.toggle_fullscreen)
        self.is_fullscreen = False
        
        # Windows taskbar icon identity
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('antigravity.ron.desktop.v2')
        except Exception:
            pass
        
        # Load custom taskbar icon (use brain logo = ron_avatar.png)
        self._load_window_icon()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # ── State ─────────────────────────────────────────────────
        self.chat_history = []          # In-memory only — for Ollama conversational context
        self.is_loading_history = False
        self.pending_reply_callback = None
        self.chat_messages_count = 0
        self.thinking_label = None
        self.thinking_dots = 0
        self.thinking_timer = None
        self.chat_history = []
        self.chat_messages_count = 0
        self.is_loading_history = False
        self.is_voice_mode = False
        
        # Load avatar images
        self._load_avatars()
        
        # Voice integration
        self.voice_manager = None
        try:
            self.voice_manager = VoiceManager()
        except Exception as e:
            print(f"Voice init error: {e}")
        
        # ── Initialize Engine ────────────────────────────────────────────────
        self.engine = RonEngine(
            ui_log_callback=self.log_to_console,
            ui_status_callback=self.update_status,
            ui_message_callback=self.display_message,
            ui_approval_callback=self.request_approval
        )
        
        # ── Layout ────────────────────────────────────────────────
        self.grid_columnconfigure(0, weight=0, minsize=280)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_sidebar()
        self._build_chat_panel()
        
        # Always start fresh
        self._new_session(show_welcome=True)
        
        # Show mode selection overlay on every startup
        self.after(100, self._show_mode_selection_screen)

    # ── Helpers ────────────────────────────────────────────────────

    def _load_window_icon(self):
        """Load custom window/taskbar icon from ron_avatar.ico/png (brain logo)."""
        try:
            icon_ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_avatar.ico")
            if os.path.exists(icon_ico_path) and sys.platform == "win32":
                self.iconbitmap(icon_ico_path)
            else:
                from PIL import Image, ImageTk
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_avatar.png")
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_logo.png")
                if os.path.exists(icon_path):
                    img = Image.open(icon_path).resize((32, 32), Image.Resampling.LANCZOS)
                    self.icon_photo = ImageTk.PhotoImage(img)
                    self.wm_iconphoto(False, self.icon_photo)
        except Exception as e:
            print(f"Failed to load icon: {e}")

    def _load_avatars(self):
        """Load Ron avatar image for chat bubbles."""
        self.ron_avatar_img = None
        try:
            from PIL import Image, ImageTk, ImageDraw
            avatar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_avatar.png")
            if os.path.exists(avatar_path):
                img = Image.open(avatar_path).resize((36, 36), Image.Resampling.LANCZOS)
                mask = Image.new("L", (36, 36), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 36, 36), fill=255)
                img.putalpha(mask)
                self.ron_avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(36, 36))
        except Exception:
            pass

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def get_timestamp(self) -> str:
        return datetime.datetime.now().strftime("%H:%M")

    # ── Mode Selection ───────────────────────────────────────────────

    def _show_mode_selection_screen(self):
        """Displays a full-screen overlay to select Offline or Online mode."""
        self.mode_overlay = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.mode_overlay.place(relwidth=1.0, relheight=1.0)
        
        container = ctk.CTkFrame(self.mode_overlay, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="Welcome to RON", font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), text_color=TEXT_PRIMARY).pack(pady=(0, 10))
        ctk.CTkLabel(container, text="Please select your preferred operating mode:", font=ctk.CTkFont(family="Segoe UI", size=16), text_color=TEXT_SECONDARY).pack(pady=(0, 30))
        
        # Offline Button
        offline_btn = ctk.CTkButton(
            container, text="🔒 Local Privacy Mode\n\nRuns entirely on your hardware\nMaximized privacy & zero data sharing",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=BG_CARD, hover_color=BORDER_DIM, text_color=TEXT_PRIMARY,
            border_width=2, border_color=TEXT_DIM,
            width=300, height=120, command=self._on_offline_selected
        )
        offline_btn.pack(side="left", padx=20)
        
        # Online Button
        online_btn = ctk.CTkButton(
            container, text="⚡ Cloud Performance Mode\n\nPowered by Google Gemini\nLightning-fast conversational speed",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            width=300, height=120, command=self._on_online_selected
        )
        online_btn.pack(side="left", padx=20)
        
    def _on_offline_selected(self):
        os.environ["RON_APP_MODE"] = "offline"
        self.mode_overlay.destroy()
        
        # Disable Voice Chat in Offline mode since Google STT uses the cloud
        if hasattr(self, 'voice_btn'):
            self.voice_btn.configure(state="disabled", fg_color=BG_CARD, text_color=TEXT_DIM)
            if hasattr(self, 'voice_tooltip'):
                self.voice_tooltip.grid(row=3, column=0, pady=(0, 4))
                
        # Hide continuous follow-up toggle since voice is disabled
        if hasattr(self, 'continuous_listening_switch'):
            self.continuous_listening_switch.grid_forget()
            
    def _on_online_selected(self):
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gemini_api_key.txt")
        if os.path.exists(key_path) and os.path.getsize(key_path) > 0:
            os.environ["RON_APP_MODE"] = "online"
            self.mode_overlay.destroy()
            
            # Enable voice features
            if hasattr(self, 'voice_btn'):
                self.voice_btn.configure(state="normal", fg_color="#059669", text_color="#FFFFFF")
                if hasattr(self, 'voice_tooltip'):
                    self.voice_tooltip.grid_forget()
            if hasattr(self, 'continuous_listening_switch'):
                self.continuous_listening_switch.grid(row=4, column=0, sticky="w", padx=20, pady=(4, 4))
        else:
            self._show_api_key_input()
            
    def _show_api_key_input(self):
        # Clear the container
        for widget in self.mode_overlay.winfo_children():
            widget.destroy()
            
        container = ctk.CTkFrame(self.mode_overlay, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="Gemini API Key Required", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=TEXT_PRIMARY).pack(pady=(0, 10))
        instructions = (
            "To unlock lightning-fast Cloud Performance Mode, you need a free Gemini API Key.\n\n"
            "1. Go to https://aistudio.google.com/app/apikey\n"
            "2. Click 'Create API Key'\n"
            "3. Paste the key below:"
        )
        ctk.CTkLabel(container, text=instructions, 
                     font=ctk.CTkFont(family="Segoe UI", size=14), text_color=TEXT_SECONDARY).pack(pady=(0, 20))
                     
        key_entry = ctk.CTkEntry(container, width=400, height=40, font=ctk.CTkFont(size=14), placeholder_text="Enter API Key here...")
        key_entry.pack(pady=(0, 20))
        
        def save_key():
            val = key_entry.get().strip()
            if val:
                key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gemini_api_key.txt")
                with open(key_path, "w", encoding="utf-8") as f:
                    f.write(val)
                os.environ["RON_APP_MODE"] = "online"
                self.mode_overlay.destroy()
                if hasattr(self, 'voice_btn'):
                    self.voice_btn.configure(state="normal", fg_color="#059669", text_color="#FFFFFF")
                    
        ctk.CTkButton(container, text="Save & Continue", command=save_key, fg_color=ACCENT, hover_color=ACCENT_HOVER, width=200, height=40, font=ctk.CTkFont(weight="bold")).pack()
        ctk.CTkButton(container, text="Cancel (Use Offline)", command=self._on_offline_selected, fg_color="transparent", hover_color=BG_CARD, text_color=TEXT_SECONDARY, width=200, height=40).pack(pady=(10, 0))

    # ── Session Management (in-memory only) ───────────────────────

    def _new_session(self, show_welcome=True):
        """Start a fresh chat — clears in-memory history and chat display."""
        self.chat_history = []
        self.chat_messages_count = 0
        
        # Clear the chat frame
        self._clear_chat_frame()
        
        if show_welcome:
            self.is_loading_history = True
            mode_text = "🔒 Local Privacy Mode" if os.environ.get("RON_APP_MODE") == "offline" else "⚡ Cloud Performance Mode"
            
            self.display_message("Ron",
                f"Hey there! 👋 I'm Ron, your AI desktop assistant.\n\n"
                f"You are currently running in **{mode_text}**.\n\n"
                "🛡️ **Safe Mode** is enabled by default at the bottom left. This acts as a security checkpoint, meaning I will always ask for your permission before executing system commands or modifying files, keeping you in full control!\n\n"
                "Here is what I can do:\n"
                "🚀  Open & close apps\n"
                "🌐  Browse the web\n"
                "⌨️  Type & automate\n"
                "📸  Take screenshots\n"
                "💻  Run commands\n\n"
                "Try asking me: \"open notepad and type hello world\"")
            self.is_loading_history = False

    # ── Sidebar ───────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)  # spacer expands
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        # ── Logo Section ──
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 0))
        
        logo_row = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_row.pack(anchor="w", fill="x")
        
        if self.ron_avatar_img:
            ctk.CTkLabel(logo_row, image=self.ron_avatar_img, text="").pack(side="left", padx=(0, 10))
        
        title_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(title_col, text="RON",
                      font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
                      text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(title_col, text="AI Desktop Agent",
                      font=ctk.CTkFont(family="Segoe UI", size=11),
                      text_color=TEXT_DIM).pack(anchor="w")
        
        # ── New Chat Button ──
        ctk.CTkButton(
            self.sidebar, text="＋  New Chat",
            command=lambda: self._new_session(show_welcome=True),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=36, corner_radius=10
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 4))
        
        # ── Voice Chat Button ──
        self.voice_btn = ctk.CTkButton(
            self.sidebar, text="🎤  Voice Chat",
            command=self.toggle_voice_mode,
            fg_color="#059669", hover_color="#047857",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=36, corner_radius=10
        )
        self.voice_btn.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 4))
        
        # Tooltip for voice button when disabled
        self.voice_tooltip = ctk.CTkLabel(
            self.sidebar, text="Requires Online Mode",
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
            text_color=DANGER
        )
        
        # ── Spacer (fills remaining space where session list used to be) ──
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.grid(row=4, column=0, sticky="nsew")
        
        # ── Continuous Listening Switch ──
        self.continuous_listening_var = ctk.BooleanVar(value=True)
        self.continuous_listening_switch = ctk.CTkSwitch(
            self.sidebar, text="Continuous Follow-up",
            variable=self.continuous_listening_var,
            onvalue=True, offvalue=False,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_DIM, button_color=ACCENT, button_hover_color=ACCENT_HOVER
        )
        self.continuous_listening_switch.grid(row=4, column=0, sticky="w", padx=20, pady=(4, 4))
        
        # ── Bottom Controls ──
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.grid(row=5, column=0, sticky="sew", padx=20, pady=(4, 4))
        
        # Status card
        self.status_card = ctk.CTkFrame(bottom, fg_color=BG_SIDEBAR_HL, corner_radius=8,
                                         border_width=1, border_color=BORDER_DIM, height=40)
        self.status_card.pack(fill="x", pady=(0, 6))
        self.status_card.pack_propagate(False)
        
        self.status_dot = ctk.CTkLabel(self.status_card, text="●",
                                        font=ctk.CTkFont(size=12), text_color=SUCCESS, width=18)
        self.status_dot.pack(side="left", padx=(12, 4))
        self.status_label = ctk.CTkLabel(self.status_card, text="Ready",
                                          font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                                          text_color=TEXT_PRIMARY)
        self.status_label.pack(side="left")
        
        # Ollama status
        self.ollama_card = ctk.CTkFrame(bottom, fg_color=BG_SIDEBAR_HL, corner_radius=8,
                                         border_width=1, border_color=BORDER_DIM, height=36)
        self.ollama_card.pack(fill="x", pady=(0, 6))
        self.ollama_card.pack_propagate(False)
        
        self.ollama_dot = ctk.CTkLabel(self.ollama_card, text="●",
                                        font=ctk.CTkFont(size=12), text_color=TEXT_DIM, width=18)
        self.ollama_dot.pack(side="left", padx=(12, 4))
        self.ollama_label = ctk.CTkLabel(self.ollama_card, text="Ollama: Checking...",
                                          font=ctk.CTkFont(family="Segoe UI", size=11),
                                          text_color=TEXT_SECONDARY)
        self.ollama_label.pack(side="left")
        self.after(500, self._check_ollama_status)
        
        # Safe Mode toggle
        self.safemode_switch = ctk.CTkSwitch(
            bottom, text="Safe Mode",
            command=self.toggle_safe_mode,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            progress_color=ACCENT, button_color=ACCENT_GLOW,
            button_hover_color=ACCENT_HOVER
        )
        self.safemode_switch.select()
        self.safemode_switch.pack(anchor="w", pady=(4, 6))
        
        # Exit button
        ctk.CTkButton(
            bottom, text="Exit Ron",
            command=self.on_closing,
            fg_color="#7F1D1D", hover_color="#991B1B", text_color="#FCA5A5",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=34, corner_radius=8
        ).pack(fill="x")

    def _check_ollama_status(self):
        import threading
        threading.Thread(target=self._check_ollama_status_thread, daemon=True).start()

    def _check_ollama_status_thread(self):
        is_online = self.engine.intent_parser.check_ollama_status()
        if is_online:
            model = self.engine.intent_parser.get_best_model_name()
            self.after(0, lambda: self._update_ollama_ui(True, model))
        else:
            self.after(0, lambda: self._update_ollama_ui(False, ""))
        
        self.after(15000, self._check_ollama_status)

    def _update_ollama_ui(self, is_online, model):
        if is_online:
            self.ollama_dot.configure(text_color=SUCCESS)
            self.ollama_label.configure(text=f"Ollama: {model}", text_color=SUCCESS)
        else:
            self.ollama_dot.configure(text_color=DANGER)
            self.ollama_label.configure(text="Ollama: Offline", text_color="#F87171")

    # ── Chat Panel ────────────────────────────────────────────────

    def _build_chat_panel(self):
        self.chat_panel = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.chat_panel.grid(row=0, column=1, sticky="nsew")
        self.chat_panel.grid_rowconfigure(1, weight=1)
        self.chat_panel.grid_rowconfigure(2, minsize=0)
        self.chat_panel.grid_columnconfigure(0, weight=1)
        
        # ── Chat Header ──
        header = ctk.CTkFrame(self.chat_panel, fg_color=BG_DARK, height=55)
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(18, 0))
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="💬  Chat",
                      font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                      text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Local & Offline  •  Your data stays on your machine",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      text_color=TEXT_DIM).grid(row=1, column=0, sticky="w")
        
        # ── Chat Messages ──
        self.chat_frame = ctk.CTkScrollableFrame(
            self.chat_panel, fg_color="transparent",
            scrollbar_button_color=BORDER_DIM,
            scrollbar_button_hover_color=TEXT_DIM
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=28, pady=(10, 6))
        self._bind_fast_scroll(self.chat_frame)
        
        # ── Approval Panel (hidden) ──
        self.approval_panel = ctk.CTkFrame(
            self.chat_panel, fg_color="#1E1B4B",
            border_color=BORDER_ACCENT, border_width=1, corner_radius=12)
        
        ctk.CTkLabel(self.approval_panel, text="🛡️  SECURITY CHECK",
                      font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                      text_color="#C7D2FE").pack(anchor="w", padx=20, pady=(12, 2))
        
        self.approval_warning_label = ctk.CTkLabel(
            self.approval_panel, text="Ron wants to execute an action.",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF", wraplength=600, justify="left")
        self.approval_warning_label.pack(anchor="w", padx=20, pady=(0, 12))
        
        btn_row = ctk.CTkFrame(self.approval_panel, fg_color="transparent")
        btn_row.pack(anchor="w", padx=20, pady=(0, 12))
        
        ctk.CTkButton(btn_row, text="✓  Approve", command=self.on_approve,
                       fg_color="#059669", hover_color="#047857", width=120,
                       font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                       corner_radius=8).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="✕  Deny", command=self.on_deny,
                       fg_color=DANGER, hover_color="#B91C1C", width=120,
                       font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                       corner_radius=8).pack(side="left")
        
        # ── Input Bar ──
        input_container = ctk.CTkFrame(self.chat_panel, fg_color="transparent")
        input_container.grid(row=3, column=0, sticky="ew", padx=28, pady=(6, 20))
        
        input_wrapper = ctk.CTkFrame(input_container, fg_color=BG_INPUT,
                                      corner_radius=14, border_width=1, border_color=BORDER_DIM)
        input_wrapper.pack(fill="x")
        
        self.input_textbox = ctk.CTkEntry(
            input_wrapper,
            placeholder_text="Message Ron... (e.g. 'open notepad and type hello world')",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=48, border_width=0, fg_color="transparent",
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM)
        self.input_textbox.pack(side="left", fill="x", expand=True, padx=(16, 8), pady=4)
        self.input_textbox.bind("<Return>", lambda e: self.send_user_instruction())
        
        self.send_btn = ctk.CTkButton(
            input_wrapper, text="➤", width=44, height=40,
            command=self.send_user_instruction,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=10)
        self.send_btn.pack(side="right", padx=(0, 5), pady=5)

    def _clear_chat_frame(self):
        """Destroy and recreate the chat scrollable frame."""
        self.chat_frame.destroy()
        self.chat_frame = ctk.CTkScrollableFrame(
            self.chat_panel, fg_color="transparent",
            scrollbar_button_color=BORDER_DIM,
            scrollbar_button_hover_color=TEXT_DIM)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=28, pady=(10, 6))
        self._bind_fast_scroll(self.chat_frame)
        self.thinking_label = None
        self.thinking_timer = None

    def _bind_fast_scroll(self, scrollable_frame):
        """Bind mousewheel for faster scrolling (3x default speed)."""
        def _on_mousewheel(event):
            scrollable_frame._parent_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
        scrollable_frame._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    # ── Thread-Safe Callbacks ─────────────────────────────────────

    def log_to_console(self, text: str):
        print(f"[Ron] {text}")

    def update_status(self, status: str):
        self.after(0, self._update_status_impl, status)

    def _update_status_impl(self, status: str):
        if hasattr(self, 'voice_manager') and self.voice_manager:
            self.voice_manager.override_status = status
            
        if "Await" in status:
            self.status_dot.configure(text_color=WARNING)
            self.status_label.configure(text="Approval", text_color=WARNING)
            self.input_textbox.configure(state="disabled")
            self.send_btn.configure(text="■", fg_color=DANGER, hover_color="#B91C1C", command=self.cancel_task)
        elif "Think" in status or "Exec" in status:
            self.status_dot.configure(text_color="#3B82F6")
            self.status_label.configure(text=status, text_color="#60A5FA")
            self.input_textbox.configure(state="disabled")
            self.send_btn.configure(text="■", fg_color=DANGER, hover_color="#B91C1C", command=self.cancel_task)
            if "Think" in status:
                self._start_thinking_animation()
        else:
            if hasattr(self, 'voice_manager') and self.voice_manager:
                self.voice_manager.override_status = None
                
                # If Voice Mode is currently active and Continuous Follow-up is on, wait for follow up
                if hasattr(self, 'is_voice_mode') and self.is_voice_mode:
                    if hasattr(self, 'continuous_listening_var') and self.continuous_listening_var.get():
                        self.voice_manager.wake_up(silent=True)
                        self.voice_manager.override_status = "Waiting for follow-up command..."
                        self.after(4000, lambda: setattr(self.voice_manager, 'override_status', None))
                        
            self.status_dot.configure(text_color=SUCCESS)
            self.status_label.configure(text="Ready", text_color=TEXT_PRIMARY)
            self.input_textbox.configure(state="normal")
            self.send_btn.configure(text="➤", fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.send_user_instruction)
            self._stop_thinking_animation()

    def cancel_task(self):
        self.engine.cancel_execution()

    # ── Thinking Animation ────────────────────────────────────────

    def _start_thinking_animation(self):
        if self.thinking_label is not None:
            return
        self.thinking_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.thinking_frame.pack(fill="x", pady=6, padx=5)
        self.thinking_label = ctk.CTkLabel(
            self.thinking_frame, text="🤖  Ron is thinking ●",
            font=ctk.CTkFont(family="Segoe UI", size=13, slant="italic"),
            text_color=ACCENT_GLOW)
        self.thinking_label.pack(anchor="w", padx=10)
        self.thinking_dots = 0
        self._animate_thinking()
        self.after(50, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def _animate_thinking(self):
        if self.thinking_label is None:
            return
        self.thinking_dots = (self.thinking_dots + 1) % 4
        dots = "●" * (self.thinking_dots + 1) + "○" * (3 - self.thinking_dots)
        self.thinking_label.configure(text=f"🤖  Ron is thinking {dots}")
        self.thinking_timer = self.after(400, self._animate_thinking)

    def _stop_thinking_animation(self):
        if self.thinking_timer:
            self.after_cancel(self.thinking_timer)
            self.thinking_timer = None
        if self.thinking_label is not None:
            self.thinking_frame.destroy()
            self.thinking_label = None

    # ── Display Messages ──────────────────────────────────────────

    def copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        old_text = self.status_label.cget("text")
        old_color = self.status_label.cget("text_color")
        self.status_label.configure(text="Copied!", text_color=WARNING)
        self.after(1200, lambda: self.status_label.configure(text=old_text, text_color=old_color))

    def display_message(self, sender: str, text: str):
        if hasattr(self, 'is_voice_mode') and self.is_voice_mode:
            if sender in ["Ron", "Ron Console"] and hasattr(self, 'voice_manager'):
                
                def _on_speak_done():
                    # If Continuous Follow-Up is on, wake him up AFTER he finishes talking!
                    if self.status_label.cget("text") in ["Ready", "Idle"]:
                        if hasattr(self, 'continuous_listening_var') and self.continuous_listening_var.get():
                            self.voice_manager.wake_up(silent=True)
                            self.voice_manager.override_status = "Waiting for follow-up command..."
                            self.after(4000, lambda: setattr(self.voice_manager, 'override_status', None))
                            
                # Speak the error or response aloud instead of writing it to chat
                self.voice_manager.speak(text, on_complete=_on_speak_done)
                
                # Briefly show it on the Voice UI as well
                self.voice_manager.override_status = f"Feedback: {text[:40]}..."
                self.after(3000, lambda: setattr(self.voice_manager, 'override_status', None))
            return
        self.after(0, self._display_message_impl, sender, text)

    def _display_message_impl(self, sender: str, text: str):
        if not text or not text.strip():
            return
        
        if sender == "Ron":
            self._stop_thinking_animation()
            if self.is_voice_mode and self.voice_manager:
                self.voice_manager.speak(text)
        
        is_user = (sender == "You")
        is_console = (sender == "Ron Console")
        
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_frame.pack(fill="x", pady=5, padx=5)
        
        align = "e" if is_user else "w"
        padx_side = (80, 4) if is_user else (4, 80)
        
        # Header
        hdr = ctk.CTkFrame(msg_frame, fg_color="transparent")
        hdr.pack(anchor=align, padx=padx_side)
        
        if not is_user and self.ron_avatar_img and not is_console:
            ctk.CTkLabel(hdr, image=self.ron_avatar_img, text="").pack(side="left", padx=(0, 8))
        
        tag = "You" if is_user else ("Console" if is_console else "Ron")
        ctk.CTkLabel(
            hdr, text=f"{tag}  •  {self.get_timestamp()}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_DIM
        ).pack(side="left")
        
        # Bubble
        if is_user:
            bubble_fg, txt_color, font_fam, font_sz = USER_BUBBLE, "#FFFFFF", "Segoe UI", 13
            border_w, border_c = 0, None
        elif is_console:
            bubble_fg, txt_color, font_fam, font_sz = CONSOLE_BG, "#38BDF8", "Consolas", 11
            border_w, border_c = 1, BORDER_DIM
        else:
            bubble_fg, txt_color, font_fam, font_sz = RON_BUBBLE, TEXT_PRIMARY, "Segoe UI", 13
            border_w, border_c = 1, "#2D3748"
        
        bubble = ctk.CTkLabel(
            msg_frame, text=text,
            font=ctk.CTkFont(family=font_fam, size=font_sz),
            text_color=txt_color, fg_color=bubble_fg,
            border_color=border_c, border_width=border_w,
            corner_radius=14, padx=18, pady=14,
            justify="left", wraplength=600, cursor="hand2")
        bubble.pack(anchor=align, padx=padx_side, pady=(3, 0))
        bubble.bind("<Button-1>", lambda e, t=text: self.copy_to_clipboard(t))
        
        self.chat_messages_count += 1
        
        # Keep in-memory history for Ollama context (never persisted to disk)
        if not self.is_loading_history and sender in ["You", "Ron"]:
            role = "user" if is_user else "assistant"
            self.chat_history.append({"role": role, "content": text})
        
        # Auto-scroll
        self.after(30, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    # ── Approval ──────────────────────────────────────────────────

    def request_approval(self, action_type: str, details: str, reply_callback: Callable[[bool], None]):
        self.after(0, self._request_approval_impl, action_type, details, reply_callback)

    def _request_approval_impl(self, action_type, details, reply_callback):
        self.pending_reply_callback = reply_callback
        desc = self.engine.safety_manager.get_action_warning(action_type, details)
        self.approval_warning_label.configure(text=desc)
        self.approval_panel.grid(row=2, column=0, sticky="ew", padx=28, pady=6)
        self.bell()

    def on_approve(self):
        self.approval_panel.grid_forget()
        if self.pending_reply_callback:
            self.pending_reply_callback(True)
            self.pending_reply_callback = None

    def on_deny(self):
        self.approval_panel.grid_forget()
        if self.pending_reply_callback:
            self.pending_reply_callback(False)
            self.pending_reply_callback = None

    # ── Voice Mode ────────────────────────────────────────────────
    
    def toggle_voice_mode(self):
        self.is_voice_mode = not self.is_voice_mode
        if self.is_voice_mode:
            # Hide the main bulky text window
            self.withdraw()
            
            # Create a small floating popup box for Voice Mode
            self.voice_window = ctk.CTkToplevel(self)
            self.voice_window.geometry("400x550")
            self.voice_window.title("Ron Voice Chat")
            
            # Use Ron avatar for the voice window icon if possible
            try:
                import sys, os
                icon_ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_avatar.ico")
                if os.path.exists(icon_ico_path) and sys.platform == "win32":
                    self.voice_window.iconbitmap(icon_ico_path)
                elif hasattr(self, 'icon_photo'):
                    self.voice_window.wm_iconphoto(False, self.icon_photo)
            except Exception:
                pass

            self.voice_window.protocol("WM_DELETE_WINDOW", self.toggle_voice_mode)
            # self.voice_window.attributes("-topmost", True) # Removed so it doesn't hover over newly opened apps
            # Build the panel inside the new window
            self._build_voice_panel(self.voice_window)
        else:
            # Switch back to text mode
            if hasattr(self, 'voice_window') and self.voice_window.winfo_exists():
                self.voice_window.destroy()
                
            self.deiconify() # Bring main window back
            self.state("zoomed")
            
            if self.voice_manager:
                self.voice_manager.stop_listening()

    def _build_voice_panel(self, parent_window):
        self.voice_panel = ctk.CTkFrame(parent_window, fg_color=BG_DARK, corner_radius=0)
        self.voice_panel.pack(fill="both", expand=True)
        
        # Large Clickable Logo
        if self.ron_avatar_img:
            try:
                import os
                from PIL import Image, ImageDraw
                avatar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_avatar.png")
                if not os.path.exists(avatar_path):
                    avatar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_logo.png")
                    
                if os.path.exists(avatar_path):
                    img = Image.open(avatar_path).resize((140, 140), Image.Resampling.LANCZOS)
                    # Convert to RGBA if not already to support transparency
                    img = img.convert("RGBA")
                    mask = Image.new("L", (140, 140), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, 140, 140), fill=255)
                    img.putalpha(mask)
                    large_img = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 140))
                    
                    logo_btn = ctk.CTkButton(
                        self.voice_panel, text="", image=large_img, 
                        fg_color="transparent", hover_color=BG_SIDEBAR_HL, 
                        width=150, height=150, corner_radius=75,
                        command=lambda: self.voice_manager.wake_up() if self.voice_manager else None
                    )
                    logo_btn.pack(expand=True, pady=(40, 10))
            except Exception as e:
                print(f"Error loading large voice avatar: {e}")
        
        self.voice_status_label = ctk.CTkLabel(
            self.voice_panel, text="Initializing...",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=ACCENT
        )
        self.voice_status_label.pack(pady=10)
        
        ctk.CTkLabel(
            self.voice_panel, text="Say 'Hey Ron' or click logo to talk",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_DIM
        ).pack(pady=5)
        
        # Microphone Selector
        mic_names = []
        try:
            import soundcard as sc
            mic_names = [m.name for m in sc.all_microphones()]
        except Exception:
            pass
            
        if mic_names:
            def on_mic_change(new_mic):
                if self.voice_manager:
                    self.voice_manager.stop_listening()
                    # Wait for thread to exit before restarting
                    self.after(500, lambda: self.voice_manager.start_listening(
                        text_callback=self._on_voice_input,
                        status_callback=self._on_voice_status,
                        mic_name=new_mic
                    ))
            
            mic_dropdown = ctk.CTkOptionMenu(
                self.voice_panel,
                values=mic_names,
                command=on_mic_change,
                fg_color=BG_DARK, button_color=BG_CARD,
                button_hover_color=BORDER_DIM, text_color=TEXT_DIM
            )
            mic_dropdown.pack(pady=10)
            
            # Start listening with currently selected dropdown value initially
            default_mic = mic_names[0]
            if self.voice_manager:
                self.voice_manager.start_listening(
                    text_callback=self._on_voice_input,
                    status_callback=self._on_voice_status,
                    mic_name=default_mic
                )
        else:
            if self.voice_manager:
                self.voice_manager.start_listening(
                    text_callback=self._on_voice_input,
                    status_callback=self._on_voice_status
                )
        
        ctk.CTkButton(
            self.voice_panel, text="🔙 Back to Text",
            command=self.toggle_voice_mode,
            fg_color=BG_CARD, hover_color=BORDER_DIM,
            text_color=TEXT_PRIMARY,
            height=40
        ).pack(side="bottom", pady=40, padx=40, fill="x")

    def _on_voice_status(self, status: str, rms_val: float = 0.0):
        if hasattr(self, "voice_status_label") and self.voice_status_label.winfo_exists():
            # Create a simple visual volume bar (max 10 blocks to stay compact)
            vol = min(int(rms_val / 50.0), 10)
            bar = "█" * vol + "░" * (10 - vol)
            
            display_text = f"{status}\n\nMic: [{bar}]"
            
            self.after(0, lambda: self.voice_status_label.configure(text=display_text))

    def _on_voice_input(self, text: str):
        self.after(0, lambda: self.display_message("You", text))
        self.after(0, lambda: self.engine.process_instruction_async(text, self.chat_history))

    # ── User Actions ──────────────────────────────────────────────

    def send_user_instruction(self):
        if self.input_textbox.cget("state") == "disabled":
            return
        text = self.input_textbox.get().strip()
        if not text:
            return
        self.input_textbox.delete(0, "end")
        self.display_message("You", text)
        self.engine.process_instruction_async(text, self.chat_history)

    def toggle_safe_mode(self):
        state = self.safemode_switch.get()
        self.engine.safety_manager.safe_mode = (state == 1)
        self.engine.safety_manager.save_settings()

    def clear_chat(self):
        """Legacy method — redirects to new session."""
        self._new_session(show_welcome=True)

    def on_closing(self):
        self.engine.set_approval(False)
        self.destroy()
        os._exit(0)


if __name__ == "__main__":
    app = RonApp()
    app.mainloop()
