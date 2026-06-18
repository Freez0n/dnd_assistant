import customtkinter as ctk
from app.database import DatabaseManager

class BestiaryView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int, add_to_combat_callback=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.add_to_combat_callback = add_to_combat_callback
        
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        control_frame = ctk.CTkFrame(self); control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(control_frame, text="👹 Личный бестиарий", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="➕ Добавить", command=self._add_monster_dialog, width=120).pack(side="left", padx=5)
        
        ctk.CTkLabel(control_frame, text="Фильтр CR: ").pack(side="left", padx=(20, 5))
        self.cr_var = ctk.StringVar(value="Все")
        ctk.CTkOptionMenu(control_frame, values=["Все", "0-1", "2-4", "5-10", "11+"], variable=self.cr_var, width=80, command=self._filter_monsters).pack(side="left", padx=5)
        
        ctk.CTkLabel(control_frame, text="Тип: ").pack(side="left", padx=(10, 5))
        self.type_var = ctk.StringVar(value="Все типы")
        ctk.CTkOptionMenu(control_frame, values=["Все типы", "Гуманоид", "Нежить", "Зверь", "Дракон", "Исчадие", "Чудовище", "Великан", "Элементаль"], variable=self.type_var, width=120, command=self._filter_monsters).pack(side="left", padx=5)
        
        self.table_scroll = ctk.CTkScrollableFrame(self); self.table_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        for i in range(7): self.table_scroll.grid_columnconfigure(i, weight=1 if i in [0, 2, 5] else 0)
        self.monster_rows = {}; self._load_monsters()

    def _load_monsters(self):
        for widget in self.table_scroll.winfo_children(): widget.destroy(); self.monster_rows = {}
        header = ctk.CTkFrame(self.table_scroll, fg_color="#2C3E50"); header.grid(row=0, column=0, columnspan=7, sticky="ew", pady=(0, 5))
        headers = ["Имя", "КД", "ХП", "Скорость", "CR", "Тип", "Действия"]
        for i, h in enumerate(headers): ctk.CTkLabel(header, text=h, font=ctk.CTkFont(weight="bold"), anchor="center" if i > 0 else "w").grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        # 🔥 ФИЛЬТРАЦИЯ ПО user_id
        query = "SELECT * FROM `monster` WHERE user_id = %s AND 1=1"; params = [self.user_id]
        if self.cr_var.get() != "Все":
            if self.cr_var.get() == "0-1": query += " AND CR >= 0 AND CR <= 1"
            elif self.cr_var.get() == "2-4": query += " AND CR >= 2 AND CR <= 4"
            elif self.cr_var.get() == "5-10": query += " AND CR >= 5 AND CR <= 10"
            elif self.cr_var.get() == "11+": query += " AND CR >= 11"
        if self.type_var.get() != "Все типы": query += " AND `Type` = %s"; params.append(self.type_var.get())
        
        monsters = self.db.fetchall(query + " ORDER BY Name", tuple(params))
        for row_idx, mon in enumerate(monsters):
            r = row_idx + 1; row_frame = ctk.CTkFrame(self.table_scroll, fg_color="#1E1E1E" if row_idx % 2 == 0 else "#252525")
            row_frame.grid(row=r, column=0, columnspan=7, sticky="ew", pady=1)
            ctk.CTkLabel(row_frame, text=mon['Name'], anchor="w", fg_color="transparent").grid(row=0, column=0, padx=10, sticky="w")
            ctk.CTkLabel(row_frame, text=str(mon['AC']), anchor="center", fg_color="transparent").grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=str(mon['HP_Avg']), anchor="center", fg_color="transparent").grid(row=0, column=2, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=mon['Speed'] or '-', anchor="center", fg_color="transparent").grid(row=0, column=3, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=str(mon['CR']), anchor="center", fg_color="transparent").grid(row=0, column=4, padx=5, sticky="ew")
            ctk.CTkLabel(row_frame, text=mon['Type'] or '-', anchor="center", fg_color="transparent").grid(row=0, column=5, padx=5, sticky="ew")
            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent"); btn_frame.grid(row=0, column=6, padx=5, sticky="e")
            ctk.CTkButton(btn_frame, text="✎", width=30, height=24, command=lambda m=mon: self._edit_monster(m)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="✕", width=30, height=24, fg_color="#E74C3C", command=lambda mid=mon['idMonster']: self._delete_monster(mid)).pack(side="left", padx=2)
            if self.add_to_combat_callback:
                ctk.CTkButton(btn_frame, text="⚔️", width=30, height=24, fg_color="#9B59B6", command=lambda m=mon: self.add_to_combat_callback(m)).pack(side="left", padx=2)
            self.monster_rows[mon['idMonster']] = row_frame

    def _filter_monsters(self, *args): self._load_monsters()

    def _add_monster_dialog(self): self._open_monster_dialog(None)
    def _edit_monster(self, mon: dict): self._open_monster_dialog(mon)

    def _open_monster_dialog(self, monster: dict):
        is_edit = monster is not None
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактировать монстра" if is_edit else "Добавить монстра")
        dialog.geometry("450x700")
        self._center_window(dialog, 450, 700)
        dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        
        scroll_frame = ctk.CTkScrollableFrame(dialog, height=600)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(scroll_frame, text="📋 Основная информация", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        ctk.CTkLabel(scroll_frame, text="Имя монстра *").pack(anchor="w", padx=5)
        name_entry = ctk.CTkEntry(scroll_frame, width=380, height=35, placeholder_text="Например: Гоблин")
        if is_edit: name_entry.insert(0, monster['Name'])
        name_entry.pack(pady=(0, 10))
        
        type_cr_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        type_cr_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(type_cr_frame, text="Тип: ").pack(side="left", padx=5)
        type_var = ctk.StringVar(value="Гуманоид")
        ctk.CTkOptionMenu(type_cr_frame, values=["Гуманоид", "Нежить", "Зверь", "Дракон", "Исчадие", "Чудовище", "Великан", "Элементаль"], variable=type_var, width=150).pack(side="left", padx=5)
        if is_edit and monster.get('Type'): type_var.set(monster['Type'])
        
        ctk.CTkLabel(type_cr_frame, text="CR: ").pack(side="left", padx=(15, 5))
        cr_entry = ctk.CTkEntry(type_cr_frame, width=80, height=30, placeholder_text="0.25")
        if is_edit: cr_entry.insert(0, str(monster['CR']))
        cr_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(scroll_frame, text="️ Боевые характеристики", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        ac_hp_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        ac_hp_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(ac_hp_frame, text="КД (AC): ").pack(side="left", padx=5)
        ac_entry = ctk.CTkEntry(ac_hp_frame, width=100, height=30, placeholder_text="10")
        if is_edit: ac_entry.insert(0, str(monster['AC']))
        ac_entry.pack(side="left", padx=5)
        ctk.CTkLabel(ac_hp_frame, text="Средний ХП: ").pack(side="left", padx=(15, 5))
        hp_entry = ctk.CTkEntry(ac_hp_frame, width=100, height=30, placeholder_text="7")
        if is_edit: hp_entry.insert(0, str(monster['HP_Avg']))
        hp_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(scroll_frame, text="Формула ХП (опционально): ").pack(anchor="w", padx=5)
        hp_formula_entry = ctk.CTkEntry(scroll_frame, width=380, height=30, placeholder_text="Например: 2d6")
        if is_edit and monster.get('HP_Formula'): hp_formula_entry.insert(0, monster['HP_Formula'])
        hp_formula_entry.pack(pady=(0, 10))
        
        ctk.CTkLabel(scroll_frame, text="Скорость: ").pack(anchor="w", padx=5)
        speed_entry = ctk.CTkEntry(scroll_frame, width=380, height=30, placeholder_text="30 фт.")
        if is_edit and monster.get('Speed'): speed_entry.insert(0, monster['Speed'])
        speed_entry.pack(pady=(0, 10))
        
        ctk.CTkLabel(scroll_frame, text="🎲 Характеристики", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        str_dex_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        str_dex_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(str_dex_frame, text="Сила: ").pack(side="left", padx=5)
        str_entry = ctk.CTkEntry(str_dex_frame, width=80, height=30, placeholder_text="10")
        if is_edit: str_entry.insert(0, str(monster['STR']))
        str_entry.pack(side="left", padx=5)
        ctk.CTkLabel(str_dex_frame, text="Ловкость: ").pack(side="left", padx=(15, 5))
        dex_entry = ctk.CTkEntry(str_dex_frame, width=80, height=30, placeholder_text="10")
        if is_edit: dex_entry.insert(0, str(monster['DEX']))
        dex_entry.pack(side="left", padx=5)
        
        con_int_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        con_int_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(con_int_frame, text="Телосложение: ").pack(side="left", padx=5)
        con_entry = ctk.CTkEntry(con_int_frame, width=80, height=30, placeholder_text="10")
        if is_edit: con_entry.insert(0, str(monster['CON']))
        con_entry.pack(side="left", padx=5)
        ctk.CTkLabel(con_int_frame, text="Интеллект: ").pack(side="left", padx=(15, 5))
        int_entry = ctk.CTkEntry(con_int_frame, width=80, height=30, placeholder_text="10")
        if is_edit: int_entry.insert(0, str(monster['INT']))
        int_entry.pack(side="left", padx=5)
        
        wis_cha_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        wis_cha_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(wis_cha_frame, text="Мудрость: ").pack(side="left", padx=5)
        wis_entry_w = ctk.CTkEntry(wis_cha_frame, width=80, height=30, placeholder_text="10")
        if is_edit: wis_entry_w.insert(0, str(monster['WIS']))
        wis_entry_w.pack(side="left", padx=5)
        ctk.CTkLabel(wis_cha_frame, text="Харизма: ").pack(side="left", padx=(15, 5))
        cha_entry = ctk.CTkEntry(wis_cha_frame, width=80, height=30, placeholder_text="10")
        if is_edit: cha_entry.insert(0, str(monster['CHA']))
        cha_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(scroll_frame, text=" Дополнительно", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        ctk.CTkLabel(scroll_frame, text="Источник (опционально): ").pack(anchor="w", padx=5)
        source_entry = ctk.CTkEntry(scroll_frame, width=380, height=30, placeholder_text="Например: MM")
        if is_edit and monster.get('Source'): source_entry.insert(0, monster['Source'])
        source_entry.pack(pady=(0, 10))
        
        def save():
            try: 
                name = name_entry.get().strip()
                if not name:
                    ctk.CTkLabel(scroll_frame, text="❌ Имя обязательно!", text_color="red").pack(pady=5)
                    return
                
                try:
                    ac = int(ac_entry.get() or 10); hp_avg = int(hp_entry.get() or 10); cr = float(cr_entry.get() or 0)
                    str_val = int(str_entry.get() or 10); dex_val = int(dex_entry.get() or 10); con_val = int(con_entry.get() or 10)
                    int_val = int(int_entry.get() or 10); wis_val = int(wis_entry_w.get() or 10); cha_val = int(cha_entry.get() or 10)
                except ValueError:
                    ctk.CTkLabel(scroll_frame, text="❌ Проверьте числовые поля!", text_color="red").pack(pady=5)
                    return
                
                hp_formula = hp_formula_entry.get().strip() or None; speed = speed_entry.get().strip() or None
                source = source_entry.get().strip() or None; monster_type = type_var.get()
                
                if is_edit:
                    self.db.execute("""UPDATE `monster` SET `Name`=%s, `AC`=%s, `HP_Formula`=%s, `HP_Avg`=%s, `Speed`=%s, 
                        `STR`=%s, `DEX`=%s, `CON`=%s, `INT`=%s, `WIS`=%s, `CHA`=%s, `CR`=%s, `Type`=%s, `Source`=%s 
                        WHERE `idMonster`=%s AND user_id=%s""", 
                        (name, ac, hp_formula, hp_avg, speed, str_val, dex_val, con_val, int_val, wis_val, cha_val, cr, monster_type, source, monster['idMonster'], self.user_id))
                else:
                    self.db.execute("""INSERT INTO `monster` (user_id, `Name`, `AC`, `HP_Formula`, `HP_Avg`, `Speed`, `STR`, `DEX`, `CON`, `INT`, `WIS`, `CHA`, `CR`, `Type`, `Source`)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                        (self.user_id, name, ac, hp_formula, hp_avg, speed, str_val, dex_val, con_val, int_val, wis_val, cha_val, cr, monster_type, source))
                
                self.db.commit(); self._load_monsters(); dialog.destroy()
            except Exception as e:
                ctk.CTkLabel(scroll_frame, text=f"❌ Ошибка: {str(e)}", text_color="red").pack(pady=5)
        
        save_btn = ctk.CTkButton(scroll_frame, text=" Сохранить", command=save, fg_color="#2ECC71", width=200, height=35, font=ctk.CTkFont(size=14, weight="bold"))
        save_btn.pack(pady=15)

    def _delete_monster(self, monster_id: int):
        dialog = ctk.CTkToplevel(self); dialog.title("Подтверждение"); dialog.geometry("350x150")
        self._center_window(dialog, 350, 150); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text="Удалить монстра?").pack(pady=15)
        def confirm(): 
            self.db.execute("DELETE FROM `monster` WHERE `idMonster` = %s AND user_id = %s", (monster_id, self.user_id))
            self.db.commit(); self._load_monsters(); dialog.destroy()
        ctk.CTkButton(dialog, text="Да", fg_color="#E74C3C", command=confirm).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(dialog, text="Отмена", command=dialog.destroy).pack(side="right", padx=20, pady=10)

    def _center_window(self, window, width, height):
        window.update_idletasks(); x = (window.winfo_screenwidth() // 2) - (width // 2); y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')