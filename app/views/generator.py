import customtkinter as ctk
from app.utils.generators import Generators

class GeneratorView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk):
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.content_frame = ctk.CTkScrollableFrame(self); self.content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.content_frame, text="🎲 Генераторы для Мастера", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=15)
        self._create_generator_block(self.content_frame, "👤 Имя НПС", self._generate_npc_name, ["Мужское", "Женское", "Любое"], "Любое")
        self._create_generator_block(self.content_frame, "📜 Завязка квеста", Generators.generate_quest_hook, None)
        traits_frame = ctk.CTkFrame(self.content_frame); traits_frame.pack(fill="x", pady=15)
        ctk.CTkLabel(traits_frame, text="🎭 Черты НПС", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        traits_grid = ctk.CTkFrame(traits_frame, fg_color="transparent"); traits_grid.pack(fill="x", padx=10)
        traits_grid.grid_columnconfigure(0, weight=1); traits_grid.grid_columnconfigure(1, weight=1)
        traits_data = [("Характер", Generators.generate_npc_trait), ("Идеал", Generators.generate_npc_ideal), ("Привязанность", Generators.generate_npc_bond), ("Изъян", Generators.generate_npc_flaw)]
        for i, (label, func) in enumerate(traits_data):
            row, col = i // 2, i % 2
            frame = ctk.CTkFrame(traits_grid); frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold")).pack(pady=(5, 2))
            result_var = ctk.StringVar(value="Нажмите 'Генерировать'")
            ctk.CTkLabel(frame, textvariable=result_var, wraplength=300, justify="left").pack(pady=2, padx=5)
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent"); btn_frame.pack(pady=5)
            ctk.CTkButton(btn_frame, text="Генерировать", width=100, height=28, command=lambda f=func, v=result_var: v.set(f())).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Копировать", width=80, height=28, command=lambda v=result_var: self._copy_to_clipboard(v.get())).pack(side="left", padx=5)
        self._create_generator_block(self.content_frame, "🌤️ Погода", Generators.generate_weather, None)
        self._create_generator_block(self.content_frame, "⚔️ Случайная встреча", Generators.generate_encounter, ["лес", "горы", "подземелье", "город", "пустошь"], "лес")
        self._create_generator_block(self.content_frame, "✨ Эффект Wild Magic", Generators.generate_wild_magic, None)
    
    def _create_generator_block(self, parent, title: str, generator_func, options: list = None, default_option: str = None):
        frame = ctk.CTkFrame(parent); frame.pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        option_var = None
        if options:
            option_var = ctk.StringVar(value=default_option)
            ctk.CTkOptionMenu(frame, values=options, variable=option_var, width=150).pack(pady=5)
        result_var = ctk.StringVar(value="Нажмите 'Генерировать'")
        ctk.CTkLabel(frame, textvariable=result_var, wraplength=800, justify="left", font=ctk.CTkFont(size=12)).pack(pady=10, padx=20)
        def generate():
            if options and option_var: result = generator_func(option_var.get())
            else: result = generator_func()
            result_var.set(result)
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent"); btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="🎲 Генерировать", command=generate, width=130, height=30).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📋 Копировать", command=lambda: self._copy_to_clipboard(result_var.get()), width=100, height=30).pack(side="left", padx=10)
    
    def _generate_npc_name(self, gender: str):
        if gender == "Мужское": return Generators.generate_npc_name("мужской")
        elif gender == "Женское": return Generators.generate_npc_name("женский")
        else: return Generators.generate_npc_name()
    
    def _copy_to_clipboard(self, text: str):
        if text and text != "Нажмите 'Генерировать'":
            self.clipboard_clear(); self.clipboard_append(text)