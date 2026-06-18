import customtkinter as ctk
from typing import Optional
from app.database import DatabaseManager
from app.utils.dice_engine import DiceEngine
import random

class CombatView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.active_session: Optional[int] = None
        self.current_turn_index: int = 0
        
        # Элементы интерфейса для вкладок
        self.tab_chars = self.tab_best = self.tab_manual = None
        self.manual_name = self.manual_hp = self.manual_ac = self.manual_init_bonus = None
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Панель управления
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(control_frame, text="⚔️ Боевой трекер", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="Новый бой", command=self._start_combat, width=100).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Добавить участника", command=self._add_participant_dialog, width=140).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Авто-инициатива", command=self._auto_initiative, width=130).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Следующий ход", command=self._next_turn, width=120).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Завершить бой", command=self._end_combat, width=120, fg_color="#E74C3C").pack(side="right", padx=5)
        
        # Таблица участников
        self.table_frame = ctk.CTkScrollableFrame(self, label_text="Участники боя")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.participant_rows = {}
        self._load_combat()

    def _start_combat(self):
        try:
            # Завершаем предыдущие активные бои этого пользователя
            self.db.execute("UPDATE `combatsession` SET IsActive = 0 WHERE IsActive = 1 AND user_id = %s", (self.user_id,))
            self.db.execute("INSERT INTO `combatsession` (user_id, IsActive) VALUES (%s, 1)", (self.user_id,))
            self.active_session = self.db.last_insert_id()
            self.db.commit()
            self._load_combat()
        except Exception as e: print(f"Ошибка начала боя: {e}")

    def _end_combat(self):
        if self.active_session: 
            self.db.execute("UPDATE `combatsession` SET IsActive = 0 WHERE idSession = %s AND user_id = %s", (self.active_session, self.user_id))
            self.db.commit()
            self.active_session = None
            self._load_combat()

    def _load_combat(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
        self.participant_rows = {}
        
        if not self.active_session: 
            ctk.CTkLabel(self.table_frame, text="Нет активной боевой сессии. Начните новый бой.", font=ctk.CTkFont(size=14)).pack(pady=40)
            return
            
        header = ctk.CTkFrame(self.table_frame, fg_color="#2C3E50")
        header.pack(fill="x", pady=(0, 5))
        headers = [" ", "Имя", "Инициатива", "ХП", "Статус", "Действия"]
        for i, h in enumerate(headers): 
            ctk.CTkLabel(header, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Загружаем только участников текущего активного боя
        participants = self.db.fetchall("""
            SELECT cp.* FROM `combatparticipant` cp 
            JOIN `combatsession` cs ON cp.idSession = cs.idSession 
            WHERE cs.user_id = %s AND cs.IsActive = 1 
            ORDER BY cp.Initiative DESC, cp.Name
        """, (self.user_id,))
        
        for idx, p in enumerate(participants):
            row = ctk.CTkFrame(self.table_frame)
            row.pack(fill="x", pady=2)
            
            # Подсветка текущего хода
            if idx == self.current_turn_index: 
                row.configure(border_width=2, border_color="#2ECC71")
                
            ctk.CTkLabel(row, text="▶ " if idx == self.current_turn_index else " ", width=20).grid(row=0, column=0, padx=5)
            ctk.CTkLabel(row, text=p['Name'], width=150, anchor="w").grid(row=0, column=1, padx=10)
            ctk.CTkLabel(row, text=f"{p['Initiative']:+d}", width=60, anchor="center").grid(row=0, column=2, padx=5)
            
            hp_frame = ctk.CTkFrame(row, fg_color="transparent")
            hp_frame.grid(row=0, column=3, padx=10)
            hp_label = ctk.CTkLabel(hp_frame, text=f"{p['CurrentHP']}/{p['MaxHP']}")
            hp_label.pack(side="left")
            if p['CurrentHP'] <= 0: 
                hp_label.configure(text="Без сознания", text_color="#E74C3C")
            
            # ✅ ЦВЕТОВАЯ ИНДИКАЦИЯ СТАТУСОВ
            status = p.get('Status', 'Нормальный') or 'Нормальный'
            if status == "Нормальный": status_color = "#2ECC71"      # Зеленый
            elif status == "Ранен": status_color = "#F39C12"        # Оранжевый
            else: status_color = "#E74C3C"                          # Красный (Без сознания)
            
            ctk.CTkLabel(row, text=status, width=100, anchor="center", text_color=status_color).grid(row=0, column=4, padx=5)
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=5, padx=5)
            ctk.CTkButton(btn_frame, text="Урон/Лечение", width=100, command=lambda pid=p['idParticipant']: self._damage_dialog(pid), height=24).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="✕", width=24, height=24, fg_color="#E74C3C", command=lambda pid=p['idParticipant']: self._remove_participant(pid)).pack(side="left", padx=2)
            
            self.participant_rows[p['idParticipant']] = {"row": row, "indicator": ctk.CTkLabel(row, text="▶ " if idx == self.current_turn_index else " ", width=20), "hp_label": hp_label}

    def _add_participant_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить участника")
        dialog.geometry("520x580")
        self._center_window(dialog, 520, 580)
        dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        
        tab_frame = ctk.CTkFrame(dialog)
        tab_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_chars = ctk.CTkButton(tab_frame, text="👥 Персонажи", command=lambda: self._switch_tab("chars"))
        self.btn_chars.pack(side="left", padx=2, pady=2, fill="x", expand=True)
        
        self.btn_best = ctk.CTkButton(tab_frame, text="👹 Бестиарий", command=lambda: self._switch_tab("best"))
        self.btn_best.pack(side="left", padx=2, pady=2, fill="x", expand=True)
        
        self.btn_manual = ctk.CTkButton(tab_frame, text="✏️ Вручную", command=lambda: self._switch_tab("manual"))
        self.btn_manual.pack(side="left", padx=2, pady=2, fill="x", expand=True)
        
        self.tab_chars = ctk.CTkScrollableFrame(dialog, height=380)
        self.tab_best = ctk.CTkScrollableFrame(dialog, height=380)
        self.tab_manual = ctk.CTkFrame(dialog)
        
        self._build_chars_tab(self.tab_chars, dialog)
        self._build_best_tab(self.tab_best, dialog)
        self._build_manual_tab(self.tab_manual, dialog)
        self._switch_tab("chars")

    def _switch_tab(self, tab_name):
        for tab in [self.tab_chars, self.tab_best, self.tab_manual]: tab.pack_forget()
        for btn in [self.btn_chars, self.btn_best, self.btn_manual]: btn.configure(fg_color="#2B2B2B")
        if tab_name == "chars": 
            self.tab_chars.pack(fill="both", expand=True, padx=10, pady=5)
            self.btn_chars.configure(fg_color="#1F6AA5")
        elif tab_name == "best": 
            self.tab_best.pack(fill="both", expand=True, padx=10, pady=5)
            self.btn_best.configure(fg_color="#1F6AA5")
        elif tab_name == "manual": 
            self.tab_manual.pack(fill="both", expand=True, padx=10, pady=5)
            self.btn_manual.configure(fg_color="#1F6AA5")
            
    def _build_chars_tab(self, frame, dialog):
        ctk.CTkLabel(frame, text="Сохранённые персонажи:", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        characters = self.db.fetchall("SELECT idCharacter, Name, Class, Level FROM `character` WHERE user_id = %s ORDER BY Name", (self.user_id,))
        if not characters: ctk.CTkLabel(frame, text="Нет сохранённых персонажей").pack(pady=20); return
        for char in characters:
            row = ctk.CTkFrame(frame); row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=f"{char['Name']} ({char['Class']} {char['Level']} ур.)", width=280, anchor="w").pack(side="left", padx=5)
            ctk.CTkButton(row, text="Добавить", width=90, height=26, fg_color="#2ECC71", command=lambda c=char: self._add_character_to_combat(c, dialog)).pack(side="right", padx=5, pady=2)

    def _build_best_tab(self, frame, dialog):
        ctk.CTkLabel(frame, text="Поиск по личному бестиарию:", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        search_entry = ctk.CTkEntry(frame, placeholder_text="Введите имя монстра..."); search_entry.pack(pady=5, padx=5, fill="x")
        list_frame = ctk.CTkFrame(frame); list_frame.pack(fill="both", expand=True, pady=5)
        def search_monsters(event=None):
            for w in list_frame.winfo_children(): w.destroy()
            q = search_entry.get().strip().lower()
            if q:
                monsters = self.db.fetchall("SELECT Name, HP_Avg, DEX, AC, CR, Type FROM `monster` WHERE user_id = %s AND LOWER(Name) LIKE %s ORDER BY Name", (self.user_id, f"%{q}%"))
            else:
                monsters = self.db.fetchall("SELECT Name, HP_Avg, DEX, AC, CR, Type FROM `monster` WHERE user_id = %s ORDER BY Name", (self.user_id,))
            if not monsters: ctk.CTkLabel(list_frame, text="Монстры не найдены").pack(pady=10)
            else:
                for m in monsters:
                    row = ctk.CTkFrame(list_frame); row.pack(fill="x", pady=2)
                    ctk.CTkLabel(row, text=f"{m['Name']} (CR {m['CR']}, {m['Type']}, ХП: {m['HP_Avg']}, КД: {m['AC']})", width=300, anchor="w").pack(side="left", padx=5)
                    ctk.CTkButton(row, text="Выбрать", width=80, height=24, fg_color="#9B59B6", command=lambda mon=m: self._select_bestiary_monster(mon)).pack(side="right", padx=5)
        search_entry.bind("<KeyRelease>", search_monsters); search_monsters()
        
    def _build_manual_tab(self, frame, dialog):
        ctk.CTkLabel(frame, text="Настройки участника:", font=ctk.CTkFont(weight="bold")).pack(pady=8)
        ctk.CTkLabel(frame, text="Имя:").pack(anchor="w", padx=15, pady=(5,0)); self.manual_name = ctk.CTkEntry(frame, width=350); self.manual_name.pack(pady=2, padx=15)
        ctk.CTkLabel(frame, text="Макс. ХП:").pack(anchor="w", padx=15, pady=(5,0)); self.manual_hp = ctk.CTkEntry(frame, width=120); self.manual_hp.insert(0, "10"); self.manual_hp.pack(pady=2, padx=15)
        ctk.CTkLabel(frame, text="КД (AC):").pack(anchor="w", padx=15, pady=(5,0)); self.manual_ac = ctk.CTkEntry(frame, width=120); self.manual_ac.insert(0, "10"); self.manual_ac.pack(pady=2, padx=15)
        ctk.CTkLabel(frame, text="Бонус инициативы:").pack(anchor="w", padx=15, pady=(5,0)); self.manual_init_bonus = ctk.CTkEntry(frame, width=120); self.manual_init_bonus.insert(0, "0"); self.manual_init_bonus.pack(pady=2, padx=15)
        ctk.CTkButton(frame, text="➕ Добавить в бой", fg_color="#2ECC71", hover_color="#27AE60", font=ctk.CTkFont(weight="bold"), command=lambda: self._add_manual_to_combat(dialog)).pack(pady=20)

    def _select_bestiary_monster(self, mon):
        self.manual_name.delete(0, "end"); self.manual_name.insert(0, mon['Name'])
        self.manual_hp.delete(0, "end"); self.manual_hp.insert(0, mon['HP_Avg'] or 10)
        self.manual_ac.delete(0, "end"); self.manual_ac.insert(0, mon['AC'] or 10)
        dex_mod = DiceEngine.calc_modifier(mon['DEX']); self.manual_init_bonus.delete(0, "end"); self.manual_init_bonus.insert(0, dex_mod)
        self._switch_tab("manual")
        
    def _add_character_to_combat(self, char, dialog):
        try:
            stats = self.db.fetchone("SELECT MaxHP, CurrentHP FROM `characterstats` WHERE idCharacter = %s", (char['idCharacter'],))
            attrs = self.db.fetchone("SELECT Dexterity FROM `attribute` WHERE idCharacter = %s", (char['idCharacter'],))
            max_hp = stats['MaxHP'] if stats else 10; dex_mod = DiceEngine.calc_modifier(attrs['Dexterity']) if attrs else 0
            initiative = random.randint(1, 20) + dex_mod
            self.db.execute("INSERT INTO `combatparticipant` (idSession, Name, Initiative, CurrentHP, MaxHP, IsPlayer, Status) VALUES (%s, %s, %s, %s, %s, 1, 'Нормальный')", (self.active_session, char['Name'], initiative, max_hp, max_hp))
            self.db.commit(); self._load_combat(); dialog.destroy()
        except Exception as e: print(f"Ошибка добавления персонажа: {e}")

    def _add_manual_to_combat(self, dialog):
        try:
            name = self.manual_name.get().strip()
            if not name: return
            max_hp = int(self.manual_hp.get() or 10); init_bonus = int(self.manual_init_bonus.get() or 0); initiative = random.randint(1, 20) + init_bonus
            self.db.execute("INSERT INTO `combatparticipant` (idSession, Name, Initiative, CurrentHP, MaxHP, IsPlayer, Status) VALUES (%s, %s, %s, %s, %s, 0, 'Нормальный')", (self.active_session, name, initiative, max_hp, max_hp))
            self.db.commit(); self._load_combat(); dialog.destroy()
        except Exception as e: print(f"Ошибка добавления вручную: {e}")

    def _auto_initiative(self):
        if not self.active_session: return
        participants = self.db.fetchall("SELECT idParticipant, Name FROM `combatparticipant` WHERE idSession = %s", (self.active_session,))
        for p in participants:
            char = self.db.fetchone("SELECT a.Dexterity FROM `character` c JOIN `attribute` a ON c.idCharacter = a.idCharacter WHERE c.Name = %s AND c.user_id = %s LIMIT 1", (p['Name'], self.user_id))
            dex_mod = DiceEngine.calc_modifier(char['Dexterity']) if char else 0; roll = random.randint(1, 20)
            self.db.execute("UPDATE `combatparticipant` SET Initiative = %s WHERE idParticipant = %s", (roll + dex_mod, p['idParticipant']))
        self.db.commit(); self._load_combat()

    def _next_turn(self):
        participants = list(self.participant_rows.keys())
        if not participants: return
        self.current_turn_index = (self.current_turn_index + 1) % len(participants); self._load_combat()

    def _damage_dialog(self, participant_id: int):
        p = self.db.fetchone("SELECT * FROM `combatparticipant` WHERE idParticipant = %s", (participant_id,))
        if not p: return
        dialog = ctk.CTkToplevel(self); dialog.title(f"Урон/Лечение: {p['Name']}"); dialog.geometry("300x200")
        self._center_window(dialog, 300, 200); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text=f"Текущие ХП: {p['CurrentHP']}/{p['MaxHP']}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(dialog, text="Значение (+ лечение, - урон)").pack(pady=5); value_entry = ctk.CTkEntry(dialog, width=150); value_entry.pack(pady=5)
        def apply():
            try:
                value = int(value_entry.get())
                new_hp = max(0, min(p['MaxHP'], p['CurrentHP'] + value))
                
                # ✅ ЛОГИКА СТАТУСОВ
                if new_hp <= 0:
                    status = "Без сознания"
                elif new_hp <= p['MaxHP'] / 2:
                    status = "Ранен"
                else:
                    status = "Нормальный"
                
                self.db.execute("UPDATE `combatparticipant` SET CurrentHP = %s, Status = %s WHERE idParticipant = %s", (new_hp, status, participant_id))
                self.db.commit(); self._load_combat(); dialog.destroy()
            except ValueError: pass
        ctk.CTkButton(dialog, text="Применить", command=apply).pack(pady=15)

    def _remove_participant(self, participant_id: int):
        self.db.execute("DELETE FROM `combatparticipant` WHERE idParticipant = %s", (participant_id,)); self.db.commit(); self._load_combat()

    def _center_window(self, window, width, height):
        window.update_idletasks(); x = (window.winfo_screenwidth() // 2) - (width // 2); y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')