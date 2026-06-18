import customtkinter as ctk
from typing import Optional, Callable
from app.database import DatabaseManager

class CharactersView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int, open_character_sheet: Callable[[int], None]):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.open_character_sheet = open_character_sheet
        
        self.grid_rowconfigure(0, weight=0); self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        top_frame = ctk.CTkFrame(self, fg_color="transparent"); top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="🔍 Поиск персонажа...", textvariable=self.search_var, width=250)
        self.search_entry.pack(side="left", padx=5); self.search_entry.bind("<KeyRelease>", self._filter_characters)
        ctk.CTkButton(top_frame, text="➕ Создать", command=self._create_character, width=100).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="🔄 Обновить", command=self._load_characters, width=100).pack(side="left", padx=5)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent"); self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.character_cards = {}; self._load_characters()

    def _load_characters(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.character_cards = {}
        characters = self.db.fetchall("SELECT * FROM `character` WHERE user_id = %s ORDER BY Name", (self.user_id,))
        for char in characters: self._create_character_card(char)

    def _create_character_card(self, char: dict):
        card = ctk.CTkFrame(self.scrollable_frame, fg_color="#1E1E1E", corner_radius=10, border_width=2, border_color="#3B8ED0")
        card.pack(fill="x", padx=10, pady=5)
        info_frame = ctk.CTkFrame(card, fg_color="transparent"); info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        ctk.CTkLabel(info_frame, text=char['Name'], font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"{char['Race'] or '—'} • {char['Class'] or '—'}", font=ctk.CTkFont(size=12), text_color="#BBBBBB").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Уровень {char['Level']} • XP: {char['Experience']}", font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w")
        
        stats = self.db.fetchone("SELECT * FROM `characterstats` WHERE idCharacter = %s", (char['idCharacter'],))
        if stats:
            hp_frame = ctk.CTkFrame(card, fg_color="transparent", width=200); hp_frame.pack(side="right", padx=10, pady=5)
            ctk.CTkLabel(hp_frame, text=f"HP: {stats['CurrentHP']}/{stats['MaxHP']}", font=ctk.CTkFont(size=10), text_color="#BBBBBB").pack()
            hp_progress = ctk.CTkProgressBar(hp_frame, width=180, progress_color="#E74C3C"); hp_progress.pack(pady=2); hp_progress.set(stats['CurrentHP'] / max(stats['MaxHP'], 1))
            
            xp_frame = ctk.CTkFrame(card, fg_color="transparent", width=200); xp_frame.pack(side="right", padx=10, pady=5)
            next_xp = self._get_next_xp(char['Level'])
            ctk.CTkLabel(xp_frame, text=f"XP: {char['Experience']}/{next_xp}", font=ctk.CTkFont(size=10), text_color="#BBBBBB").pack()
            xp_progress = ctk.CTkProgressBar(xp_frame, width=180, progress_color="#2ECC71"); xp_progress.pack(pady=2); xp_progress.set(char['Experience'] / max(next_xp, 1))
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent"); btn_frame.pack(side="right", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="📋 Открыть", width=100, command=lambda cid=char['idCharacter']: self.open_character_sheet(cid)).pack(pady=2)
        ctk.CTkButton(btn_frame, text="✏️ Редактировать", width=100, command=lambda cid=char['idCharacter']: self._edit_character(cid)).pack(pady=2)
        ctk.CTkButton(btn_frame, text="️Удалить      ", width=100, fg_color="#E74C3C", hover_color="#C0392B", command=lambda cid=char['idCharacter']: self._delete_character(cid)).pack(pady=2)
        self.character_cards[char['idCharacter']] = card

    def _filter_characters(self, event=None): 
        search_term = self.search_var.get().lower()
        for char_id, card in self.character_cards.items():
            char = self.db.fetchone("SELECT * FROM `character` WHERE idCharacter = %s AND user_id = %s", (char_id, self.user_id))
            if char and (search_term in char['Name'].lower() or search_term in (char['Race'] or '').lower() or search_term in (char['Class'] or '').lower()):
                 card.pack(fill="x", padx=10, pady=5)
            else: card.pack_forget()

    def _create_character(self):
        dialog = ctk.CTkToplevel(self); dialog.title("Создание персонажа"); dialog.geometry("400x350")
        self._center_window(dialog, 400, 350); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text="Имя персонажа*").pack(pady=5); name_entry = ctk.CTkEntry(dialog, width=300); name_entry.pack(pady=5)
        ctk.CTkLabel(dialog, text="Раса").pack(pady=5); race_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Человек, Эльф, Дварф..."); race_entry.pack(pady=5)
        ctk.CTkLabel(dialog, text="Класс").pack(pady=5); class_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Воин, Волшебник, Плут..."); class_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            if not name: ctk.CTkLabel(dialog, text="❌ Имя обязательно!", text_color="red").pack(pady=5); return
            try:
                self.db.execute("INSERT INTO `character` (user_id, Name, Race, Class) VALUES (%s, %s, %s, %s)", (self.user_id, name, race_entry.get(), class_entry.get()))
                char_id = self.db.last_insert_id()
                for tbl in ["`attribute`", "`characterstats`", "`savingthrowsproficiency`", "`savingthrows`", "`skillproficiency`", "`skill`"]:
                    self.db.execute(f"INSERT INTO {tbl} (idCharacter) VALUES (%s)", (char_id,))
                self.db.commit(); self._load_characters(); dialog.destroy()
            except Exception as e: ctk.CTkLabel(dialog, text=f"❌ Ошибка: {str(e)}", text_color="red").pack(pady=5)
        ctk.CTkButton(dialog, text="Создать", command=save, fg_color="#2ECC71").pack(pady=20)

    def _edit_character(self, char_id: int):
        char = self.db.fetchone("SELECT * FROM `character` WHERE idCharacter = %s AND user_id = %s", (char_id, self.user_id))
        stats = self.db.fetchone("SELECT * FROM `characterstats` WHERE idCharacter = %s", (char_id,))
        if not char: return
        dialog = ctk.CTkToplevel(self); dialog.title("Редактирование персонажа"); dialog.geometry("450x520")
        self._center_window(dialog, 450, 520); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text="Имя*").pack(pady=5); name_entry = ctk.CTkEntry(dialog, width=350); name_entry.insert(0, char['Name']); name_entry.pack(pady=5)
        ctk.CTkLabel(dialog, text="Раса").pack(pady=5); race_entry = ctk.CTkEntry(dialog, width=350); race_entry.insert(0, char['Race'] or ''); race_entry.pack(pady=5)
        ctk.CTkLabel(dialog, text="Класс").pack(pady=5); class_entry = ctk.CTkEntry(dialog, width=350); class_entry.insert(0, char['Class'] or ''); class_entry.pack(pady=5)
        ctk.CTkLabel(dialog, text="Опыт").pack(pady=5); xp_entry = ctk.CTkEntry(dialog, width=150); xp_entry.insert(0, str(char['Experience'])); xp_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="⚔️ Боевые характеристики", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        stats_frame = ctk.CTkFrame(dialog); stats_frame.pack(pady=5)
        fields = [("Макс. HP:", "MaxHP"), ("Текущие HP:", "CurrentHP"), ("КД (AC):", "ArmorClass"), ("Скорость:", "Speed")]
        for i, (lbl, key) in enumerate(fields):
            r, c = divmod(i, 2); ctk.CTkLabel(stats_frame, text=lbl).grid(row=r, column=c*2, padx=5, pady=2)
            entry = ctk.CTkEntry(stats_frame, width=80); entry.insert(0, str(stats[key] if stats else 10)); entry.grid(row=r, column=c*2+1, padx=5, pady=2)
            setattr(self, f"edit_{key}", entry)
            
        def save():
            try:
                self.db.execute("UPDATE `character` SET Name=%s, Race=%s, Class=%s, Experience=%s WHERE idCharacter=%s AND user_id=%s",
                              (name_entry.get(), race_entry.get(), class_entry.get(), int(xp_entry.get() or 0), char_id, self.user_id))
                self.db.execute("UPDATE `characterstats` SET MaxHP=%s, CurrentHP=%s, ArmorClass=%s, Speed=%s WHERE idCharacter=%s",
                              (int(self.edit_MaxHP.get() or 10), int(self.edit_CurrentHP.get() or 10), int(self.edit_ArmorClass.get() or 10), int(self.edit_Speed.get() or 30), char_id))
                self._update_character_level(char_id); self.db.commit(); self._load_characters(); dialog.destroy()
            except Exception as e: ctk.CTkLabel(dialog, text=f"❌ Ошибка: {str(e)}", text_color="red").pack(pady=5)
        ctk.CTkButton(dialog, text="💾 Сохранить", command=save, fg_color="#2ECC71").pack(pady=20)

    def _delete_character(self, char_id: int):
        char = self.db.fetchone("SELECT Name FROM `character` WHERE idCharacter = %s AND user_id = %s", (char_id, self.user_id))
        if not char: return
        dialog = ctk.CTkToplevel(self); dialog.title("⚠️ Подтверждение удаления"); dialog.geometry("400x180")
        self._center_window(dialog, 400, 180); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        msg = f'Удалить персонажа "{char["Name"]}"?\n\n️ Все связанные данные будут удалены!'
        ctk.CTkLabel(dialog, text=msg, justify="center").pack(pady=15)
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent"); btn_frame.pack(pady=10)
        def confirm():
            try:
                tables_to_delete = ["`item`", "`skill`", "`skillproficiency`", "`savingthrows`", "`savingthrowsproficiency`", "`characterstats`", "`attribute`"]
                for table in tables_to_delete:
                    try: self.db.execute(f"DELETE FROM {table} WHERE idCharacter = %s", (char_id,))
                    except: pass
                self.db.execute("DELETE FROM `character` WHERE idCharacter = %s AND user_id = %s", (char_id, self.user_id))
                self.db.commit(); self._load_characters(); dialog.destroy()
            except Exception as e: ctk.CTkLabel(dialog, text=f" Ошибка: {str(e)}", text_color="red").pack()
        ctk.CTkButton(btn_frame, text="🗑️ Да, удалить", fg_color="#E74C3C", hover_color="#C0392B", command=confirm).pack(side="left", padx=20)
        ctk.CTkButton(btn_frame, text="Отмена", command=dialog.destroy).pack(side="left", padx=20)

    def _update_character_level(self, char_id: int):
        char = self.db.fetchone("SELECT Experience FROM `character` WHERE idCharacter = %s AND user_id = %s", (char_id, self.user_id))
        if not char: return
        level_data = self.db.fetchone("SELECT Level, ProficiencyBonus FROM `experiencelevelmap` WHERE user_id = %s AND MinExperience <= %s ORDER BY MinExperience DESC LIMIT 1", (self.user_id, char['Experience']))
        if level_data: self.db.execute("UPDATE `character` SET Level = %s, ProficiencyBonus = %s WHERE idCharacter = %s AND user_id = %s", (level_data['Level'], level_data['ProficiencyBonus'], char_id, self.user_id))

    def _get_next_xp(self, level: int) -> int:
        xp_map = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000, 999999]
        return xp_map[min(level, 20)]

    def _center_window(self, window, width, height):
        window.update_idletasks(); x = (window.winfo_screenwidth() // 2) - (width // 2); y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')