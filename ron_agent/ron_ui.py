import os
import sys
import json
import uuid
import tkinter as tk
import customtkinter as ctk
from typing import Callable
import datetime

# Import local packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ron_agent.ron_engine import RonEngine

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

# ── Sessions Directory ─────────────────────────────────────────────
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


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
        self.chat_history = []
        self.is_loading_history = True
        self.pending_reply_callback = None
        self.chat_messages_count = 0
        self.thinking_label = None
        self.thinking_dots = 0
        self.thinking_timer = None
        
        # Session management
        self.current_session_id = None
        self.sessions_index = []  # [{id, title, timestamp}, ...]
        self._load_sessions_index()
        
        # Load avatar images
        self._load_avatars()
        
        # ── Engine ────────────────────────────────────────────────
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
        
        # Start a new session or load the latest one
        if self.sessions_index:
            self._load_session(self.sessions_index[0]["id"])
        else:
            self._new_session(show_welcome=True)

    # ── Helpers ────────────────────────────────────────────────────

    def _load_window_icon(self):
        """Load custom window/taskbar icon from ron_avatar.png (brain logo)."""
        try:
            from PIL import Image, ImageTk
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_avatar.png")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ron_logo.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path).resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(False, self.icon_photo)
        except Exception:
            pass

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

    # ── Session Management ────────────────────────────────────────

    def _sessions_index_path(self) -> str:
        return os.path.join(SESSIONS_DIR, "_index.json")

    def _session_file_path(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")

    def _load_sessions_index(self):
        """Load the sessions index from disk."""
        path = self._sessions_index_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.sessions_index = json.load(f)
            except Exception:
                self.sessions_index = []
        else:
            self.sessions_index = []
            # Migrate old chat_history.json if it exists
            old_history = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")
            if os.path.exists(old_history):
                try:
                    with open(old_history, "r", encoding="utf-8") as f:
                        old_msgs = json.load(f)
                    if old_msgs:
                        sid = str(uuid.uuid4())[:8]
                        first_msg = old_msgs[0].get("content", "Chat")[:40] if old_msgs else "Chat"
                        session_data = {"messages": old_msgs}
                        with open(self._session_file_path(sid), "w", encoding="utf-8") as f:
                            json.dump(session_data, f, indent=2, ensure_ascii=False)
                        self.sessions_index.insert(0, {
                            "id": sid,
                            "title": first_msg,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                        self._save_sessions_index()
                except Exception:
                    pass

    def _save_sessions_index(self):
        try:
            with open(self._sessions_index_path(), "w", encoding="utf-8") as f:
                json.dump(self.sessions_index, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _save_current_session(self):
        """Save current chat history to the session file."""
        if not self.current_session_id or not self.chat_history:
            return
        try:
            data = {"messages": self.chat_history}
            with open(self._session_file_path(self.current_session_id), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _new_session(self, show_welcome=True):
        """Create a new chat session."""
        # Save current session first
        self._save_current_session()
        
        sid = str(uuid.uuid4())[:8]
        self.current_session_id = sid
        self.chat_history = []
        self.chat_messages_count = 0
        
        # Clear the chat frame
        self._clear_chat_frame()
        
        if show_welcome:
            self.is_loading_history = True
            self.display_message("Ron",
                "Hey there! 👋 I'm Ron, your local AI desktop assistant.\n\n"
                "I run completely offline on your machine. Here's what I can do:\n\n"
                "🚀  Open & close apps\n"
                "🌐  Browse the web\n"
                "⌨️  Type & automate\n"
                "📸  Screenshots\n"
                "🔊  Volume control\n"
                "💻  Run commands\n\n"
                "Try: \"open notepad and type hello world\"")
            self.is_loading_history = False
        
        # Session gets added to index on first user message (so empty sessions aren't saved)

    def _load_session(self, session_id: str):
        """Load a specific session by ID."""
        self._save_current_session()
        
        path = self._session_file_path(session_id)
        if not os.path.exists(path):
            self._new_session()
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_session_id = session_id
            self.chat_history = data.get("messages", [])
            self.chat_messages_count = 0
            
            self._clear_chat_frame()
            
            self.is_loading_history = True
            for msg in self.chat_history:
                sender = "You" if msg.get("role") == "user" else "Ron"
                self.display_message(sender, msg.get("content", ""))
            self.is_loading_history = False
            
            # Update sidebar highlight
            self._refresh_session_list()
        except Exception:
            self._new_session()

    def _delete_session(self, session_id: str):
        """Delete a session from index and disk."""
        self.sessions_index = [s for s in self.sessions_index if s["id"] != session_id]
        self._save_sessions_index()
        try:
            path = self._session_file_path(session_id)
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        if session_id == self.current_session_id:
            if self.sessions_index:
                self._load_session(self.sessions_index[0]["id"])
            else:
                self._new_session()
        else:
            self._refresh_session_list()

    def _ensure_session_in_index(self, first_message: str):
        """Add current session to index if it isn't already there."""
        for s in self.sessions_index:
            if s["id"] == self.current_session_id:
                return
        title = first_message[:40].strip()
        if not title:
            title = "New Chat"
        self.sessions_index.insert(0, {
            "id": self.current_session_id,
            "title": title,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._save_sessions_index()
        self._refresh_session_list()

    # ── Sidebar ───────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)  # session list expands
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
        
        # Divider
        ctk.CTkFrame(self.sidebar, fg_color=BORDER_DIM, height=1).grid(
            row=2, column=0, sticky="ew", padx=20, pady=(10, 6))
        
        # ── Chat History Label ──
        ctk.CTkLabel(
            self.sidebar, text="CHAT HISTORY",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=TEXT_DIM
        ).grid(row=3, column=0, sticky="w", padx=24, pady=(4, 2))
        
        # ── Session List (scrollable) ──
        self.session_list_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=BORDER_DIM,
            scrollbar_button_hover_color=TEXT_DIM
        )
        self.session_list_frame.grid(row=4, column=0, sticky="nsew", padx=8, pady=(0, 4))
        # Faster scrolling for session list
        self._bind_fast_scroll(self.session_list_frame)
        
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
        
        # Populate session list
        self._refresh_session_list()

    def _refresh_session_list(self):
        """Rebuild the session list buttons in the sidebar."""
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()
        
        for session in self.sessions_index:
            sid = session["id"]
            title = session.get("title", "Chat")[:35]
            ts = session.get("timestamp", "")
            try:
                dt = datetime.datetime.fromisoformat(ts)
                date_str = dt.strftime("%b %d, %H:%M")
            except Exception:
                date_str = ""
            
            is_active = (sid == self.current_session_id)
            fg = BG_SIDEBAR_HL if is_active else "transparent"
            border_c = ACCENT if is_active else BG_SIDEBAR
            border_w = 1 if is_active else 0
            
            row_frame = ctk.CTkFrame(self.session_list_frame, fg_color=fg, corner_radius=8,
                                      border_color=border_c, border_width=border_w)
            row_frame.pack(fill="x", pady=2, padx=4)
            
            btn = ctk.CTkButton(
                row_frame, text=f"💬  {title}",
                command=lambda s=sid: self._load_session(s),
                fg_color="transparent", hover_color=BG_SIDEBAR_HL,
                text_color=TEXT_PRIMARY if is_active else TEXT_SECONDARY,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w", height=32
            )
            btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
            
            if date_str:
                ctk.CTkLabel(
                    row_frame, text=date_str,
                    font=ctk.CTkFont(family="Segoe UI", size=9),
                    text_color=TEXT_DIM
                ).pack(side="right", padx=(0, 8))
            
            # Delete button (small X)
            del_btn = ctk.CTkButton(
                row_frame, text="✕", width=24, height=24,
                command=lambda s=sid: self._delete_session(s),
                fg_color="transparent", hover_color="#7F1D1D",
                text_color=TEXT_DIM,
                font=ctk.CTkFont(size=11), corner_radius=4
            )
            del_btn.pack(side="right", padx=(0, 2))

    def _check_ollama_status(self):
        is_online = self.engine.intent_parser.check_ollama_status()
        if is_online:
            model = self.engine.intent_parser.get_best_model_name()
            self.ollama_dot.configure(text_color=SUCCESS)
            self.ollama_label.configure(text=f"Ollama: {model}", text_color=SUCCESS)
        else:
            self.ollama_dot.configure(text_color=DANGER)
            self.ollama_label.configure(text="Ollama: Offline", text_color="#F87171")
        self.after(15000, self._check_ollama_status)

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
        self.after(0, self._display_message_impl, sender, text)

    def _display_message_impl(self, sender: str, text: str):
        if not text or not text.strip():
            return
        
        if sender == "Ron":
            self._stop_thinking_animation()
        
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
        
        # Persist to history
        if not self.is_loading_history and sender in ["You", "Ron"]:
            role = "user" if is_user else "assistant"
            self.chat_history.append({"role": role, "content": text})
            self._save_current_session()
            
            # Add session to index on first user message
            if is_user and self.chat_messages_count == 1:
                self._ensure_session_in_index(text)
        
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
        """Legacy method — now redirects to new session."""
        self._new_session(show_welcome=True)

    def on_closing(self):
        self._save_current_session()
        self.engine.set_approval(False)
        self.destroy()
        os._exit(0)


if __name__ == "__main__":
    app = RonApp()
    app.mainloop()
