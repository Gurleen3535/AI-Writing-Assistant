import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont
import customtkinter as ctk
from typing import Callable
import time
import threading
from groq import Groq
import PyPDF2
from docx import Document

GROQ_API_KEY = "YOUR_API_KEY"

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    groq_client = None
    print(f"Warning: Groq API not initialized. Error: {e}")

MODELS = {
    "summarizer": "llama-3.1-8b-instant",
    "humanizer": "llama-3.3-70b-versatile",
    "essay": "llama-3.3-70b-versatile",
    "story": "llama-3.3-70b-versatile"
}

def call_groq_api(prompt: str, model_key: str, max_tokens: int = 2000) -> str:
    if not groq_client:
        return "Error: API not configured. Please add your Groq API key."
    try:
        model = MODELS.get(model_key, "llama-3.1-8b-instant")
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error calling API: {str(e)}\n\nPlease check your API key and internet connection."

def read_text_from_file(path: str) -> str:
    try:
        if path.lower().endswith(".txt"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif path.lower().endswith(".pdf"):
            text = ""
            with open(path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text if text.strip() else "Could not extract text from PDF"
        elif path.lower().endswith(".docx"):
            doc = Document(path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text if text.strip() else "Could not extract text from DOCX"
        elif path.lower().endswith(".doc"):
            return "Legacy .doc format not supported. Please convert to .docx or .pdf"
        else:
            return f"Unsupported file format: {path.split('.')[-1]}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

LIGHT_BG = "#F8F9FA"
CARD_BG = "#FFFFFF"
DARK_BG = "#1A1D23"
DARK_CARD = "#252932"
ACCENT_SUMMARIZER = "#4A90E2"
ACCENT_SUMMARIZER_HOVER = "#357ABD"
ACCENT_HUMANIZER = "#50C878"
ACCENT_HUMANIZER_HOVER = "#45B369"
ACCENT_ESSAY = "#9B59B6"
ACCENT_ESSAY_HOVER = "#8E44AD"
ACCENT_STORY = "#FF6B6B"
ACCENT_STORY_HOVER = "#E85A5A"
PRIMARY_TEXT = "#2C3E50"
SECONDARY_TEXT = "#7F8C8D"
LIGHT_TEXT = "#ECF0F1"
BORDER_COLOR = "#E1E8ED"
SHADOW_COLOR = "#00000015"
SUCCESS_COLOR = "#27AE60"
WARNING_COLOR = "#F39C12"
BTN_SECONDARY = "#95A5A6"
BTN_SECONDARY_HOVER = "#7F8C8D"

class EnhancedButton(ctk.CTkButton):
    def __init__(self, master, icon_text="", **kwargs):
        text = kwargs.get('text', '')
        if icon_text:
            kwargs['text'] = f"{icon_text}  {text}"
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    def _on_enter(self, e=None):
        self.configure(cursor="hand2")
    def _on_leave(self, e=None):
        self.configure(cursor="")

class LoadingIndicator(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.dots = 0
        self.is_loading = False
        self.label = ctk.CTkLabel(self, text="Processing", font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT_SUMMARIZER)
        self.label.pack()
    def start(self):
        self.is_loading = True
        self._animate()
    def stop(self):
        self.is_loading = False
    def _animate(self):
        if not self.is_loading:
            return
        self.dots = (self.dots + 1) % 4
        self.label.configure(text=f"Processing{'.' * self.dots}")
        self.after(300, self._animate)

class ShadowCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=16, border_width=0, fg_color=CARD_BG, **kwargs)

class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=30, fg_color=CARD_BG, **kwargs)
        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=11), text_color=SECONDARY_TEXT)
        self.status_label.pack(side="left", padx=10)
        self.version_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10), text_color=SECONDARY_TEXT)
        self.version_label.pack(side="right", padx=10)
    def set_status(self, text: str, color: str = None):
        self.status_label.configure(text=text)
        if color:
            self.status_label.configure(text_color=color)
        else:
            self.status_label.configure(text_color=SECONDARY_TEXT)

class AIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Writing Assistant")
        self.geometry("1400x900")
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        available = set(tkfont.families())
        if "Segoe UI" in available:
            family = "Segoe UI"
        elif "Arial" in available:
            family = "Arial"
        else:
            family = tkfont.nametofont("TkDefaultFont").actual()["family"]
        self.FONT_TITLE = ctk.CTkFont(family=family, size=44, weight="bold")
        self.FONT_SUBTITLE = ctk.CTkFont(family=family, size=16)
        self.FONT_HDR = ctk.CTkFont(family=family, size=20, weight="bold")
        self.FONT_TEXT = ctk.CTkFont(family=family, size=13)
        self.FONT_BTN = ctk.CTkFont(family=family, size=15, weight="bold")
        self.FONT_SMALL = ctk.CTkFont(family=family, size=11)
        self.is_dark = False
        self.configure(fg_color=LIGHT_BG)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.main_container = ctk.CTkFrame(master=self, fg_color=LIGHT_BG)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.pages = {}
        for P in (HomePage, SummarizerPage, HumanizerPage, EssayWriterPage, StoryGeneratorPage):
            page = P(parent=self.main_container, controller=self)
            self.pages[P.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")
        self.show_page("HomePage")
    def show_page(self, name: str):
        page = self.pages.get(name)
        if page:
            page.tkraise()
            self.status_bar.set_status(f"Navigated to {name.replace('Page', '')}")
    def toggle_theme(self, to_dark: bool):
        self.is_dark = bool(to_dark)
        ctk.set_appearance_mode("Dark" if self.is_dark else "Light")
        bg = DARK_BG if self.is_dark else LIGHT_BG
        self.configure(fg_color=bg)
        self.main_container.configure(fg_color=bg)
        for p in self.pages.values():
            if hasattr(p, "refresh_theme"):
                p.refresh_theme()
        self.status_bar.set_status(f"Theme changed to {'Dark' if self.is_dark else 'Light'}")

class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller: AIApp):
        super().__init__(master=parent, fg_color=LIGHT_BG)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        center = ctk.CTkFrame(master=self, fg_color="transparent")
        center.grid(row=0, column=0)
        switch_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        switch_frame.place(relx=0.95, rely=0.05, anchor="ne")
        self.dark_var = ctk.BooleanVar(value=controller.is_dark)
        self.theme_switch = ctk.CTkSwitch(master=switch_frame, text="🌙 Dark Mode", variable=self.dark_var, command=lambda: controller.toggle_theme(self.dark_var.get()))
        self.theme_switch.pack()
        title = ctk.CTkLabel(master=center, text="A.I. Writing Assistant", font=controller.FONT_TITLE, text_color=PRIMARY_TEXT)
        title.pack(pady=(0, 10))
        subtitle = ctk.CTkLabel(master=center, text="✨ Elevate your writing with AI-powered tools", font=controller.FONT_SUBTITLE, text_color=SECONDARY_TEXT)
        subtitle.pack(pady=(0, 40))
        btn_cfg = dict(width=420, height=75, corner_radius=38, font=controller.FONT_BTN)
        b1 = EnhancedButton(master=center, icon_text="📝", text="AI Summarizer", command=lambda: controller.show_page("SummarizerPage"), fg_color=ACCENT_SUMMARIZER, hover_color=ACCENT_SUMMARIZER_HOVER, **btn_cfg)
        b1.pack(pady=12)
        b2 = EnhancedButton(master=center, icon_text="✍️", text="AI Humanizer", command=lambda: controller.show_page("HumanizerPage"), fg_color=ACCENT_HUMANIZER, hover_color=ACCENT_HUMANIZER_HOVER, **btn_cfg)
        b2.pack(pady=12)
        b3 = EnhancedButton(master=center, icon_text="📄", text="Essay Writer", command=lambda: controller.show_page("EssayWriterPage"), fg_color=ACCENT_ESSAY, hover_color=ACCENT_ESSAY_HOVER, **btn_cfg)
        b3.pack(pady=12)
        b4 = EnhancedButton(master=center, icon_text="📖", text="Story Generator", command=lambda: controller.show_page("StoryGeneratorPage"), fg_color=ACCENT_STORY, hover_color=ACCENT_STORY_HOVER, **btn_cfg)
        b4.pack(pady=12)
    def refresh_theme(self):
        bg = DARK_BG if self.controller.is_dark else LIGHT_BG
        self.configure(fg_color=bg)

class SummarizerPage(ctk.CTkFrame):
    def __init__(self, parent, controller: AIApp):
        super().__init__(master=parent, fg_color=LIGHT_BG)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        center = ctk.CTkFrame(master=self, fg_color="transparent")
        center.grid(row=0, column=0, padx=80, pady=20, sticky="nsew")
        title = ctk.CTkLabel(master=center, text="📝 AI Summarizer", font=controller.FONT_TITLE, text_color=PRIMARY_TEXT)
        title.pack(pady=(0, 15))
        self.seg_var = ctk.StringVar(value="Summary")
        seg = ctk.CTkSegmentedButton(master=center, values=["Summary", "Bullets"], variable=self.seg_var, corner_radius=10, selected_color=ACCENT_SUMMARIZER, selected_hover_color=ACCENT_SUMMARIZER_HOVER)
        seg.pack(pady=(0, 12))
        card = ShadowCard(master=center)
        card.pack(fill="both", expand=True, pady=(0, 12))
        self.summary_text = ctk.CTkTextbox(master=card, wrap="word", font=controller.FONT_TEXT, width=1100, height=450, border_width=0, corner_radius=12)
        self.summary_text.pack(padx=15, pady=15, fill="both", expand=True)
        bottom = ctk.CTkFrame(master=card, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=(0, 15))
        self.word_label = ctk.CTkLabel(bottom, text="📊 0 Words", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT)
        self.word_label.pack(side="left")
        dl_btn = EnhancedButton(master=bottom, icon_text="💾", text="Download", width=140, corner_radius=10, command=self._download, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER)
        dl_btn.pack(side="right", padx=(5, 0))
        copy_btn = EnhancedButton(master=bottom, icon_text="📋", text="Copy", width=120, corner_radius=10, command=self._copy, fg_color=SUCCESS_COLOR, hover_color="#229954")
        copy_btn.pack(side="right")
        self.loading = LoadingIndicator(center)
        action_frame = ctk.CTkFrame(master=center, fg_color="transparent")
        action_frame.pack(pady=(0, 8))
        upload_btn = EnhancedButton(master=action_frame, icon_text="📁", text="Upload File", width=220, corner_radius=22, command=self._upload, fg_color=ACCENT_SUMMARIZER, hover_color=ACCENT_SUMMARIZER_HOVER)
        upload_btn.pack(side="left", padx=5)
        summarize_btn = EnhancedButton(master=action_frame, icon_text="✨", text="Summarize", width=220, corner_radius=22, command=self._summarize, fg_color=ACCENT_SUMMARIZER, hover_color=ACCENT_SUMMARIZER_HOVER)
        summarize_btn.pack(side="left", padx=5)
        home_btn = EnhancedButton(master=center, icon_text="🏠", text="Home", width=180, corner_radius=22, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER, command=lambda: controller.show_page("HomePage"))
        home_btn.pack(pady=(8, 0))
        self.summary_text.bind("<KeyRelease>", lambda e: self._update_wordcount())
    def _update_wordcount(self):
        txt = self.summary_text.get("1.0", "end-1c")
        words = len(txt.split())
        self.word_label.configure(text=f"📊 {words} Words")
    def _copy(self):
        txt = self.summary_text.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to copy", WARNING_COLOR)
            return
        self.controller.clipboard_clear()
        self.controller.clipboard_append(txt)
        self.controller.status_bar.set_status("✅ Copied to clipboard!", SUCCESS_COLOR)
        messagebox.showinfo("Success", "Summary copied to clipboard!")
    def _download(self):
        txt = self.summary_text.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to save", WARNING_COLOR)
            messagebox.showwarning("Empty", "No text to save.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            self.controller.status_bar.set_status(f"✅ Saved to {p}", SUCCESS_COLOR)
            messagebox.showinfo("Success", f"Saved to {p}")
    def _upload(self):
        p = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("PDF", "*.pdf"), ("Word", "*.docx"), ("All files", "*.*")])
        if not p:
            return
        self.controller.status_bar.set_status("📂 Loading file...")
        content = read_text_from_file(p)
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", content)
        self._update_wordcount()
        self.controller.status_bar.set_status("✅ File loaded successfully!", SUCCESS_COLOR)
    def _summarize(self):
        txt = self.summary_text.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ No text to summarize", WARNING_COLOR)
            messagebox.showwarning("Empty", "Please enter or upload text first.")
            return
        self.controller.status_bar.set_status("⏳ Summarizing with AI...")
        self.loading.pack(pady=10)
        self.loading.start()
        threading.Thread(target=self._run_summarize, args=(txt,), daemon=True).start()
    def _run_summarize(self, text):
        format_type = self.seg_var.get()
        if format_type == "Bullets":
            prompt = f"""Summarize the following text into clear, concise bullet points. Extract only the key information and main ideas:

{text}

Provide a bullet-point summary:"""
        else:
            prompt = f"""Provide a concise summary of the following text. Capture the main ideas and key points in a clear, readable format:

{text}

Summary:"""
        result = call_groq_api(prompt, "summarizer", max_tokens=1500)
        self.after(0, self._finish_summarize, result)
    def _finish_summarize(self, result):
        self.loading.stop()
        self.loading.pack_forget()
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", result)
        self._update_wordcount()
        self.controller.status_bar.set_status("✅ Summary generated!", SUCCESS_COLOR)
    def refresh_theme(self):
        bg = DARK_BG if self.controller.is_dark else LIGHT_BG
        self.configure(fg_color=bg)

class HumanizerPage(ctk.CTkFrame):
    def __init__(self, parent, controller: AIApp):
        super().__init__(master=parent, fg_color=LIGHT_BG)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        center = ctk.CTkFrame(master=self, fg_color="transparent")
        center.grid(row=0, column=0, padx=80, pady=20, sticky="nsew")
        title = ctk.CTkLabel(master=center, text="✍️ AI Humanizer", font=controller.FONT_TITLE, text_color=PRIMARY_TEXT)
        title.pack(pady=(0, 20))
        card = ShadowCard(master=center)
        card.pack(fill="both", expand=True, pady=(0, 12))
        self.human_text = ctk.CTkTextbox(master=card, wrap="word", font=controller.FONT_TEXT, width=1100, height=480, border_width=0, corner_radius=12)
        self.human_text.pack(padx=15, pady=15, fill="both", expand=True)
        bottom = ctk.CTkFrame(master=card, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=(0, 15))
        self.word_label = ctk.CTkLabel(bottom, text="📊 0 Words", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT)
        self.word_label.pack(side="left")
        dl_btn = EnhancedButton(master=bottom, icon_text="💾", text="Download", width=140, corner_radius=10, command=self._download, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER)
        dl_btn.pack(side="right", padx=(5, 0))
        copy_btn = EnhancedButton(master=bottom, icon_text="📋", text="Copy", width=120, corner_radius=10, command=self._copy, fg_color=SUCCESS_COLOR, hover_color="#229954")
        copy_btn.pack(side="right")
        self.loading = LoadingIndicator(center)
        action_frame = ctk.CTkFrame(master=center, fg_color="transparent")
        action_frame.pack(pady=(0, 8))
        upload_btn = EnhancedButton(master=action_frame, icon_text="📁", text="Upload File", width=220, corner_radius=22, command=self._upload, fg_color=ACCENT_HUMANIZER, hover_color=ACCENT_HUMANIZER_HOVER)
        upload_btn.pack(side="left", padx=5)
        humanize_btn = EnhancedButton(master=action_frame, icon_text="✨", text="Humanize", width=220, corner_radius=22, command=self._humanize, fg_color=ACCENT_HUMANIZER, hover_color=ACCENT_HUMANIZER_HOVER)
        humanize_btn.pack(side="left", padx=5)
        home_btn = EnhancedButton(master=center, icon_text="🏠", text="Home", width=180, corner_radius=22, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER, command=lambda: controller.show_page("HomePage"))
        home_btn.pack(pady=(8, 0))
        self.human_text.bind("<KeyRelease>", lambda e: self._update_wordcount())
    def _update_wordcount(self):
        txt = self.human_text.get("1.0", "end-1c")
        words = len(txt.split())
        self.word_label.configure(text=f"📊 {words} Words")
    def _copy(self):
        txt = self.human_text.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to copy", WARNING_COLOR)
            return
        self.controller.clipboard_clear()
        self.controller.clipboard_append(txt)
        self.controller.status_bar.set_status("✅ Copied to clipboard!", SUCCESS_COLOR)
        messagebox.showinfo("Success", "Text copied to clipboard!")
    def _download(self):
        txt = self.human_text.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to save", WARNING_COLOR)
            messagebox.showwarning("Empty", "Nothing to save.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            self.controller.status_bar.set_status(f"✅ Saved to {p}", SUCCESS_COLOR)
            messagebox.showinfo("Success", f"Saved to {p}")
    def _upload(self):
        p = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("PDF", "*.pdf"), ("Word", "*.docx"), ("All files", "*.*")])
        if not p:
            return
        self.controller.status_bar.set_status("📂 Loading file...")
        content = read_text_from_file(p)
        self.human_text.delete("1.0", "end")
        self.human_text.insert("1.0", content)
        self._update_wordcount()
        self.controller.status_bar.set_status("✅ File loaded successfully!", SUCCESS_COLOR)
    def _humanize(self):
        txt = self.human_text.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ No text to humanize", WARNING_COLOR)
            messagebox.showwarning("Empty", "Please enter or upload text first.")
            return
        self.controller.status_bar.set_status("⏳ Humanizing with AI...")
        self.loading.pack(pady=10)
        self.loading.start()
        threading.Thread(target=self._run_humanize, args=(txt,), daemon=True).start()
    def _run_humanize(self, text):
        prompt = f"""Rewrite the following text to make it sound more natural, human, and conversational while preserving the original meaning and key information. Make it engaging and authentic:

{text}

Humanized version:"""
        result = call_groq_api(prompt, "humanizer", max_tokens=2500)
        self.after(0, self._finish_humanize, result)
    def _finish_humanize(self, result):
        self.loading.stop()
        self.loading.pack_forget()
        self.human_text.delete("1.0", "end")
        self.human_text.insert("1.0", result)
        self._update_wordcount()
        self.controller.status_bar.set_status("✅ Text humanized!", SUCCESS_COLOR)
    def refresh_theme(self):
        bg = DARK_BG if self.controller.is_dark else LIGHT_BG
        self.configure(fg_color=bg)

class EssayWriterPage(ctk.CTkFrame):
    def __init__(self, parent, controller: AIApp):
        super().__init__(master=parent, fg_color=LIGHT_BG)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        center = ctk.CTkFrame(master=self, fg_color="transparent")
        center.grid(row=0, column=0, padx=60, pady=20, sticky="nsew")
        center.grid_columnconfigure(0, weight=0)
        center.grid_columnconfigure(1, weight=1)
        center.grid_rowconfigure(1, weight=1)
        title = ctk.CTkLabel(master=center, text="📄 Essay Writer", font=controller.FONT_TITLE, text_color=PRIMARY_TEXT)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        left = ctk.CTkFrame(master=center, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(master=left, text="Essay Topic:", font=controller.FONT_HDR, text_color=PRIMARY_TEXT, anchor="w").pack(fill="x", pady=(0, 5))
        self.topic_entry = ctk.CTkEntry(master=left, width=420, height=38, placeholder_text="Enter your essay topic...", border_width=2, corner_radius=10)
        self.topic_entry.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(master=left, text="Keywords (optional):", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.keywords = ctk.CTkEntry(master=left, placeholder_text="comma, separated, keywords", height=32, border_width=2, corner_radius=10)
        self.keywords.pack(fill="x", pady=(3, 10))
        ctk.CTkLabel(master=left, text="Target Audience:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.audience = ctk.CTkEntry(master=left, placeholder_text="e.g., University Students", height=32, border_width=2, corner_radius=10)
        self.audience.pack(fill="x", pady=(3, 12))
        opts_frame = ctk.CTkFrame(master=left, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(0, 10))
        left_opt = ctk.CTkFrame(master=opts_frame, fg_color="transparent")
        left_opt.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(master=left_opt, text="Type:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.essay_type = ctk.CTkOptionMenu(master=left_opt, values=["Narrative", "Descriptive", "Argumentative", "Expository"], fg_color=ACCENT_ESSAY, button_color=ACCENT_ESSAY_HOVER, button_hover_color=ACCENT_ESSAY_HOVER)
        self.essay_type.set("Narrative")
        self.essay_type.pack(fill="x", pady=(3, 0))
        right_opt = ctk.CTkFrame(master=opts_frame, fg_color="transparent")
        right_opt.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(master=right_opt, text="Length:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.essay_length = ctk.CTkOptionMenu(master=right_opt, values=["Short (500w)", "Standard (1000w)", "Long (2000w)"], fg_color=ACCENT_ESSAY, button_color=ACCENT_ESSAY_HOVER, button_hover_color=ACCENT_ESSAY_HOVER)
        self.essay_length.set("Standard (1000w)")
        self.essay_length.pack(fill="x", pady=(3, 0))
        self.create_outline = ctk.CTkCheckBox(master=left, text="📋 Create Outline First", checkbox_width=20, checkbox_height=20)
        self.create_outline.pack(anchor="w", pady=(8, 4))
        self.add_reference = ctk.CTkCheckBox(master=left, text="📚 Add References", checkbox_width=20, checkbox_height=20)
        self.add_reference.pack(anchor="w", pady=4)
        self.bypass_ai = ctk.CTkCheckBox(master=left, text="🔓 Bypass AI Detection", checkbox_width=20, checkbox_height=20)
        self.bypass_ai.pack(anchor="w", pady=4)
        ctk.CTkLabel(master=left, text="Tone:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x", pady=(10, 3))
        self.tone = ctk.CTkOptionMenu(master=left, values=["Professional", "Casual", "Academic", "Creative"], fg_color=ACCENT_ESSAY, button_color=ACCENT_ESSAY_HOVER, button_hover_color=ACCENT_ESSAY_HOVER)
        self.tone.set("Professional")
        self.tone.pack(fill="x")
        right = ctk.CTkFrame(master=center, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(15, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(master=right, text="Generated Essay", font=controller.FONT_HDR, text_color=PRIMARY_TEXT, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 5))
        result_card = ShadowCard(master=right)
        result_card.grid(row=1, column=0, sticky="nsew")
        result_card.grid_rowconfigure(0, weight=1)
        result_card.grid_columnconfigure(0, weight=1)
        self.essay_result = ctk.CTkTextbox(master=result_card, wrap="word", font=controller.FONT_TEXT, border_width=0, corner_radius=12)
        self.essay_result.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        result_bottom = ctk.CTkFrame(master=result_card, fg_color="transparent")
        result_bottom.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        result_bottom.grid_columnconfigure(0, weight=1)
        self.word_count = ctk.CTkLabel(result_bottom, text="📊 0 Words", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT)
        self.word_count.grid(row=0, column=0, sticky="w")
        dl_btn = EnhancedButton(master=result_bottom, icon_text="💾", text="Download", width=125, corner_radius=10, command=self._download, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER)
        dl_btn.grid(row=0, column=2, padx=(5, 0))
        copy_btn = EnhancedButton(master=result_bottom, icon_text="📋", text="Copy", width=105, corner_radius=10, command=self._copy, fg_color=SUCCESS_COLOR, hover_color="#229954")
        copy_btn.grid(row=0, column=1)
        self.loading = LoadingIndicator(center)
        gen_btn = EnhancedButton(master=center, icon_text="✨", text="Generate Essay", width=400, height=50, corner_radius=25, fg_color=ACCENT_ESSAY, hover_color=ACCENT_ESSAY_HOVER, command=self._generate)
        gen_btn.grid(row=2, column=0, columnspan=2, pady=(12, 8))
        home_btn = EnhancedButton(master=center, icon_text="🏠", text="Home", width=170, corner_radius=22, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER, command=lambda: controller.show_page("HomePage"))
        home_btn.grid(row=3, column=0, columnspan=2, pady=(0, 0))
    def _generate(self):
        topic = self.topic_entry.get().strip()
        if not topic:
            self.controller.status_bar.set_status("⚠️ Please enter a topic", WARNING_COLOR)
            messagebox.showwarning("Missing Topic", "Please enter an essay topic.")
            return
        self.controller.status_bar.set_status("⏳ Generating essay with AI...")
        self.loading.grid(row=2, column=0, columnspan=2, pady=10)
        self.loading.start()
        threading.Thread(target=self._run_generate, daemon=True).start()
    def _run_generate(self):
        topic = self.topic_entry.get().strip()
        essay_type = self.essay_type.get()
        length = self.essay_length.get()
        tone = self.tone.get()
        keywords = self.keywords.get().strip()
        audience = self.audience.get().strip()
        length_words = "500" if "500" in length else "1000" if "1000" in length else "2000"
        prompt = f"""Write a {essay_type.lower()} essay on the topic: "{topic}"

Requirements:
- Type: {essay_type}
- Length: Approximately {length_words} words
- Tone: {tone}"""
        if audience:
            prompt += f"\n- Target Audience: {audience}"
        if keywords:
            prompt += f"\n- Include these keywords naturally: {keywords}"
        prompt += """

The essay should include:
1. A compelling introduction with a clear thesis statement
2. Well-structured body paragraphs with supporting evidence and examples
3. A strong conclusion that ties everything together

Write the complete essay:"""
        result = call_groq_api(prompt, "essay", max_tokens=3000)
        self.after(0, self._finish_generate, result)
    def _finish_generate(self, result):
        self.loading.stop()
        self.loading.grid_forget()
        self.essay_result.delete("1.0", "end")
        self.essay_result.insert("1.0", result)
        self._update_count()
        self.controller.status_bar.set_status("✅ Essay generated!", SUCCESS_COLOR)
    def _update_count(self):
        txt = self.essay_result.get("1.0", "end-1c")
        words = len(txt.split())
        self.word_count.configure(text=f"📊 {words} Words")
    def _copy(self):
        txt = self.essay_result.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to copy", WARNING_COLOR)
            return
        self.controller.clipboard_clear()
        self.controller.clipboard_append(txt)
        self.controller.status_bar.set_status("✅ Copied to clipboard!", SUCCESS_COLOR)
        messagebox.showinfo("Success", "Essay copied to clipboard!")
    def _download(self):
        txt = self.essay_result.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to save", WARNING_COLOR)
            messagebox.showwarning("Empty", "Nothing to save.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            self.controller.status_bar.set_status(f"✅ Saved to {p}", SUCCESS_COLOR)
            messagebox.showinfo("Success", f"Saved to {p}")
    def refresh_theme(self):
        bg = DARK_BG if self.controller.is_dark else LIGHT_BG
        self.configure(fg_color=bg)

class StoryGeneratorPage(ctk.CTkFrame):
    def __init__(self, parent, controller: AIApp):
        super().__init__(master=parent, fg_color=LIGHT_BG)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        center = ctk.CTkFrame(master=self, fg_color="transparent")
        center.grid(row=0, column=0, padx=60, pady=20, sticky="nsew")
        center.grid_columnconfigure(0, weight=0)
        center.grid_columnconfigure(1, weight=1)
        center.grid_rowconfigure(1, weight=1)
        title = ctk.CTkLabel(master=center, text="📖 Story Generator", font=controller.FONT_TITLE, text_color=PRIMARY_TEXT)
        title.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        left = ctk.CTkFrame(master=center, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(master=left, text="Story Title:", font=controller.FONT_HDR, text_color=PRIMARY_TEXT, anchor="w").pack(fill="x", pady=(0, 5))
        self.story_title = ctk.CTkEntry(master=left, width=420, height=38, placeholder_text="Write your story title here...", border_width=2, corner_radius=10)
        self.story_title.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(master=left, text="Genre:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.genre = ctk.CTkOptionMenu(master=left, values=["Fantasy", "Sci-fi", "Romance", "Thriller"], fg_color=ACCENT_STORY, button_color=ACCENT_STORY_HOVER, button_hover_color=ACCENT_STORY_HOVER)
        self.genre.set("Fantasy")
        self.genre.pack(fill="x", pady=(3, 10))
        ctk.CTkLabel(master=left, text="Main Characters:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.characters = ctk.CTkEntry(master=left, placeholder_text="Protagonist, Antagonist...", height=32, border_width=2, corner_radius=10)
        self.characters.pack(fill="x", pady=(3, 10))
        ctk.CTkLabel(master=left, text="Key Plot Points:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x")
        self.plot1 = ctk.CTkEntry(master=left, placeholder_text="Plot point 1", height=32, border_width=2, corner_radius=10)
        self.plot1.pack(fill="x", pady=(3, 6))
        self.plot2 = ctk.CTkEntry(master=left, placeholder_text="Plot point 2", height=32, border_width=2, corner_radius=10)
        self.plot2.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(master=left, text="Story Length:", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT, anchor="w").pack(fill="x", pady=(8, 3))
        length_frame = ctk.CTkFrame(master=left, fg_color="transparent")
        length_frame.pack(fill="x", pady=(0, 10))
        self.length_var = ctk.StringVar(value="Short (2k)")
        short_btn = ctk.CTkRadioButton(master=length_frame, text="Short (2k)", variable=self.length_var, value="Short (2k)")
        short_btn.pack(side="left", padx=(0, 12))
        novella_btn = ctk.CTkRadioButton(master=length_frame, text="Novel (10k)", variable=self.length_var, value="Novella (10k)")
        novella_btn.pack(side="left")
        self.develop_chars = ctk.CTkCheckBox(master=left, text="🎭 Develop Character Arcs", checkbox_width=20, checkbox_height=20)
        self.develop_chars.pack(anchor="w", pady=(8, 4))
        self.plot_twists = ctk.CTkCheckBox(master=left, text="🎬 Include Plot Twists", checkbox_width=20, checkbox_height=20)
        self.plot_twists.pack(anchor="w", pady=4)
        right = ctk.CTkFrame(master=center, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(15, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(master=right, text="Generated Story", font=controller.FONT_HDR, text_color=PRIMARY_TEXT, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 5))
        result_card = ShadowCard(master=right)
        result_card.grid(row=1, column=0, sticky="nsew")
        result_card.grid_rowconfigure(0, weight=1)
        result_card.grid_columnconfigure(0, weight=1)
        self.story_result = ctk.CTkTextbox(master=result_card, wrap="word", font=controller.FONT_TEXT, border_width=0, corner_radius=12)
        self.story_result.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        result_bottom = ctk.CTkFrame(master=result_card, fg_color="transparent")
        result_bottom.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        result_bottom.grid_columnconfigure(0, weight=1)
        self.word_count = ctk.CTkLabel(result_bottom, text="📊 0 Words", font=controller.FONT_SMALL, text_color=SECONDARY_TEXT)
        self.word_count.grid(row=0, column=0, sticky="w")
        dl_btn = EnhancedButton(master=result_bottom, icon_text="💾", text="Download", width=125, corner_radius=10, command=self._download, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER)
        dl_btn.grid(row=0, column=2, padx=(5, 0))
        copy_btn = EnhancedButton(master=result_bottom, icon_text="📋", text="Copy", width=105, corner_radius=10, command=self._copy, fg_color=SUCCESS_COLOR, hover_color="#229954")
        copy_btn.grid(row=0, column=1)
        self.loading = LoadingIndicator(center)
        gen_btn = EnhancedButton(master=center, icon_text="✨", text="Generate Story", width=400, height=50, corner_radius=25, fg_color=ACCENT_STORY, hover_color=ACCENT_STORY_HOVER, command=self._generate)
        gen_btn.grid(row=2, column=0, columnspan=2, pady=(12, 8))
        home_btn = EnhancedButton(master=center, icon_text="🏠", text="Home", width=170, corner_radius=22, fg_color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER, command=lambda: controller.show_page("HomePage"))
        home_btn.grid(row=3, column=0, columnspan=2, pady=(0, 0))
    def _generate(self):
        title = self.story_title.get().strip()
        if not title:
            self.controller.status_bar.set_status("⚠️ Please enter a story title", WARNING_COLOR)
            messagebox.showwarning("Missing Title", "Please enter a story title.")
            return
        self.controller.status_bar.set_status("⏳ Generating story with AI...")
        self.loading.grid(row=2, column=0, columnspan=2, pady=10)
        self.loading.start()
        threading.Thread(target=self._run_generate, daemon=True).start()
    def _run_generate(self):
        title = self.story_title.get().strip()
        genre = self.genre.get()
        length = self.length_var.get()
        characters = self.characters.get().strip()
        plot1 = self.plot1.get().strip()
        plot2 = self.plot2.get().strip()
        length_words = "2000" if "2k" in length else "10000"
        prompt = f"""Write a creative {genre.lower()} story titled "{title}"

Requirements:
- Genre: {genre}
- Length: Approximately {length_words} words"""
        if characters:
            prompt += f"\n- Main Characters: {characters}"
        if plot1:
            prompt += f"\n- Include this plot element: {plot1}"
        if plot2:
            prompt += f"\n- Include this plot element: {plot2}"
        prompt += """

The story should:
- Have an engaging opening that hooks the reader
- Include vivid descriptions and compelling dialogue
- Build tension and conflict naturally
- Feature character development
- Have a satisfying resolution

Write the complete story:"""
        result = call_groq_api(prompt, "story", max_tokens=4000)
        self.after(0, self._finish_generate, result)
    def _finish_generate(self, result):
        self.loading.stop()
        self.loading.grid_forget()
        self.story_result.delete("1.0", "end")
        self.story_result.insert("1.0", result)
        self._update_count()
        self.controller.status_bar.set_status("✅ Story generated!", SUCCESS_COLOR)
    def _update_count(self):
        txt = self.story_result.get("1.0", "end-1c")
        words = len(txt.split())
        self.word_count.configure(text=f"📊 {words} Words")
    def _copy(self):
        txt = self.story_result.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to copy", WARNING_COLOR)
            return
        self.controller.clipboard_clear()
        self.controller.clipboard_append(txt)
        self.controller.status_bar.set_status("✅ Copied to clipboard!", SUCCESS_COLOR)
        messagebox.showinfo("Success", "Story copied to clipboard!")
    def _download(self):
        txt = self.story_result.get("1.0", "end-1c")
        if not txt.strip():
            self.controller.status_bar.set_status("⚠️ Nothing to save", WARNING_COLOR)
            messagebox.showwarning("Empty", "Nothing to save.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            self.controller.status_bar.set_status(f"✅ Saved to {p}", SUCCESS_COLOR)
            messagebox.showinfo("Success", f"Saved to {p}")
    def refresh_theme(self):
        bg = DARK_BG if self.controller.is_dark else LIGHT_BG
        self.configure(fg_color=bg)

if __name__ == "__main__":
    app = AIApp()
    app.mainloop()