import customtkinter as ctk
from typing import Optional, Dict, Any
from app.database import DatabaseManager
from app.utils.dice_engine import DiceEngine

class CharacterSheetView(ctk.CTkFrame):
    SKILL_ATTR_MAP = {"Acrobatics": "Dexterity", "SleightOfHand": "Dexterity", "Stealth": "Dexterity", "Athletics": "Strength", "AnimalHandling": "Wisdom", "Insight": "Wisdom", "Medicine": "Wisdom", "Perception": "Wisdom", "Survival": "Wisdom", "Deception": "Charisma", "Intimidation": "Charisma", "Performance": "Charisma", "Persuasion": "Charisma", "History": "Intelligence", "Investigation": "Intelligence", "Nature": "Intelligence", "Religion": "Intelligence"}
    ATTR_RUS = {"Strength": "Сила", "Dexterity": "Ловкость", "Constitution": "Телосложение", "Intelligence": "Интеллект", "Wisdom": "Мудрость", "Charisma": "Харизма"}
    SKILL_RUS = {"Acrobatics": "Акробатика", "AnimalHandling": "Обращение с животными", "Athletics": "Атлетика", "Deception": "Обман", "History": "История", "Insight": "Проницательность", "Intimidation": "Запугивание", "Investigation": "Расследование", "Medicine": "Медицина", "Nature": "Природа", "Perception": "Внимательность", "Performance": "Выступление", "Persuasion": "Убеждение", "Religion": "Религия", "SleightOfHand": "Ловкость рук", "Stealth": "Скрытность", "Survival": "Выживание"}
    
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int):
        super().__init__(parent); self.db = db; self.user_id = user_id; self.parent_window = parent; self.current_char_id: Optional[int] = None; self.entries: Dict[str, Any] = {}; self.checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.grid_rowconfigure(0, weight=0); self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        self.header = ctk.CTkFrame(self, fg_color="transparent"); self.header.grid(row=0, column=0, sticky="ew", padx=15, pady=8)
        self.title_lbl = ctk.CTkLabel(self.header, text="📋 Лист персонажа", font=ctk.CTkFont(size=16, weight="bold")); self.title_lbl.pack(side="left", padx=5)
        self.name_lbl = ctk.CTkLabel(self.header, text="", font=ctk.CTkFont(size=14)); self.name_lbl.pack(side="left", padx=15)
        btn_frame = ctk.CTkFrame(self.header, fg_color="transparent"); btn_frame.pack(side="right")
        self.save_btn = ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self._save_all, width=110, fg_color="#2ECC71"); self.save_btn.pack(side="left", padx=5)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent"); self.scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.scroll.grid_columnconfigure(0, weight=1); self.scroll.grid_columnconfigure(1, weight=1); self.scroll.grid_columnconfigure(2, weight=1)
        self._build_sections(); self._set_empty_state()

    def _set_empty_state(self):
        self.name_lbl.configure(text="Персонаж не выбран")
        for w in self.entries.values():
            try: w.delete(0, "end") if hasattr(w, "delete") else w.configure(text="0")
            except: pass
        for cb in self.checkboxes.values():
            try: cb.deselect()
            except: pass

    def _build_sections(self):
        pad = {"padx": 8, "pady": 6}
        sec1 = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E"); sec1.grid(row=0, column=0, columnspan=3, sticky="ew", **pad)
        ctk.CTkLabel(sec1, text="🧙 Основная информация", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(8, 4))
        fields = [("Имя", "name", "readonly"), ("Раса", "race", "normal"), ("Класс", "class_", "normal"), ("Уровень", "level", "normal"), ("Опыт", "experience", "normal"), ("Бонус мастерства", "prof_bonus", "normal")]
        for i, (lbl, key, state) in enumerate(fields):
            r, c = divmod(i, 3); ctk.CTkLabel(sec1, text=lbl+": ", width=100, anchor="e").grid(row=r+1, column=c*2, **pad, sticky="e")
            e = ctk.CTkEntry(sec1, width=150); e.grid(row=r+1, column=c*2+1, **pad, sticky="w"); e.configure(state=state)
            if key == "experience": e.bind("<KeyRelease>", lambda ev: self._on_stat_change())
            elif key in ["level", "prof_bonus"]: e.bind("<FocusOut>", lambda ev: self._recalculate())
            self.entries[key] = e

        sec2 = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E"); sec2.grid(row=1, column=0, columnspan=3, sticky="ew", **pad)
        ctk.CTkLabel(sec2, text=" Атрибуты & Спасброски", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(8, 4))
        for i, attr in enumerate(self.ATTR_RUS.keys()):
            r, c = divmod(i, 3); box = ctk.CTkFrame(sec2, fg_color="#2A2A2A", corner_radius=6); box.grid(row=r+1, column=c, padx=10, pady=4, sticky="ew"); box.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(box, text=self.ATTR_RUS[attr], font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(6, 2))
            score = ctk.CTkEntry(box, width=60, justify="center"); score.grid(row=1, column=0, pady=2); score.bind("<KeyRelease>", lambda ev, k=attr: self._recalculate()); self.entries[f"{attr}_score"] = score
            mod = ctk.CTkLabel(box, text="+0", font=ctk.CTkFont(weight="bold", size=15), text_color="#2ECC71"); mod.grid(row=2, column=0, pady=2); self.entries[f"{attr}_mod"] = mod
            save_row = ctk.CTkFrame(box, fg_color="transparent"); save_row.grid(row=3, column=0, pady=(4, 6), sticky="ew"); save_row.grid_columnconfigure(0, weight=1); save_row.grid_columnconfigure(1, weight=0)
            cb = ctk.CTkCheckBox(save_row, text="Владение", command=self._recalculate); cb.grid(row=0, column=0, sticky="w", padx=10); self.checkboxes[f"save_{attr}"] = cb
            total = ctk.CTkLabel(save_row, text="+0", width=35, font=ctk.CTkFont(weight="bold")); total.grid(row=0, column=1, sticky="e", padx=10); self.entries[f"save_{attr}_total"] = total

        sec3 = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E"); sec3.grid(row=2, column=0, columnspan=3, sticky="ew", **pad)
        ctk.CTkLabel(sec3, text="⚔️ Боевые характеристики", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=5, sticky="w", padx=10, pady=(8, 4))
        stats = [("MaxHP", "Макс. ХП"), ("CurrentHP", "Текущие ХП"), ("ArmorClass", "Класс доспеха"), ("Speed", "Скорость")]
        for i, (key, lbl) in enumerate(stats):
            ctk.CTkLabel(sec3, text=lbl+": ", width=110, anchor="e").grid(row=1, column=i*2, **pad, sticky="e")
            e = ctk.CTkEntry(sec3, width=100); e.grid(row=1, column=i*2+1, **pad, sticky="w"); e.bind("<KeyRelease>", lambda ev: self._recalculate()); self.entries[key] = e
        ctk.CTkLabel(sec3, text="Инициатива (авто): ", width=110, anchor="e").grid(row=1, column=4, **pad, sticky="e")
        init = ctk.CTkEntry(sec3, width=100, state="readonly"); init.grid(row=1, column=5, **pad, sticky="w"); self.entries["Initiative"] = init

        sec4 = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E"); sec4.grid(row=3, column=0, columnspan=3, sticky="ew", **pad)
        ctk.CTkLabel(sec4, text="🎯 Навыки", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 4))
        skills = list(self.SKILL_ATTR_MAP.keys())
        for i, skill in enumerate(skills):
            r, c = divmod(i, 3); row = ctk.CTkFrame(sec4, fg_color="#2A2A2A", corner_radius=4); row.grid(row=r+1, column=c, padx=10, pady=2, sticky="ew"); row.grid_columnconfigure(0, weight=1)
            cb = ctk.CTkCheckBox(row, text="", command=self._recalculate, width=20); cb.grid(row=0, column=0, sticky="w", padx=8); self.checkboxes[f"skill_{skill}"] = cb
            ctk.CTkLabel(row, text=self.SKILL_RUS[skill], anchor="w").grid(row=0, column=1, sticky="w", padx=5)
            total = ctk.CTkLabel(row, text="+0", width=30, font=ctk.CTkFont(weight="bold"), anchor="e"); total.grid(row=0, column=2, sticky="e", padx=8); self.entries[f"skill_{skill}_total"] = total

        sec5 = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E"); sec5.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)
        ctk.CTkLabel(sec5, text="📝 Особенности / Заметки", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))
        self.entries["notes"] = ctk.CTkTextbox(sec5, height=80); self.entries["notes"].pack(fill="x", padx=10, pady=(0, 8))

    def load_character(self, char_id: int):
        char = self.db.fetchone("SELECT * FROM `character` WHERE idCharacter = %s AND user_id = %s", (char_id, self.user_id))
        if not char: return
        attrs = self.db.fetchone("SELECT * FROM `attribute` WHERE idCharacter = %s", (char_id,))
        stats = self.db.fetchone("SELECT * FROM `characterstats` WHERE idCharacter = %s", (char_id,))
        save_p = self.db.fetchone("SELECT * FROM `savingthrowsproficiency` WHERE idCharacter = %s", (char_id,))
        skill_p = self.db.fetchone("SELECT * FROM `skillproficiency` WHERE idCharacter = %s", (char_id,))
        if not all([char, attrs, stats]): return
        self.current_char_id = char_id
        self.title_lbl.configure(text=f"📋 {char['Name']}"); self.name_lbl.configure(text=char['Name'])
        self.entries["name"].configure(state="normal"); self.entries["name"].delete(0, "end"); self.entries["name"].insert(0, char['Name']); self.entries["name"].configure(state="readonly")
        self.entries["race"].configure(state="normal"); self.entries["race"].delete(0, "end"); self.entries["race"].insert(0, char['Race'] or '')
        self.entries["class_"].configure(state="normal"); self.entries["class_"].delete(0, "end"); self.entries["class_"].insert(0, char['Class'] or '')
        self.entries["level"].configure(state="normal"); self.entries["level"].delete(0, "end"); self.entries["level"].insert(0, char['Level']); self.entries["level"].configure(state="readonly")
        self.entries["experience"].configure(state="normal"); self.entries["experience"].delete(0, "end"); self.entries["experience"].insert(0, char['Experience'])
        self.entries["prof_bonus"].configure(state="normal"); self.entries["prof_bonus"].delete(0, "end"); self.entries["prof_bonus"].insert(0, char['ProficiencyBonus']); self.entries["prof_bonus"].configure(state="readonly")
        for a in self.ATTR_RUS.keys(): self.entries[f"{a}_score"].delete(0, "end"); self.entries[f"{a}_score"].insert(0, attrs[a])
        for s in ["MaxHP", "CurrentHP", "ArmorClass", "Speed"]: self.entries[s].delete(0, "end"); self.entries[s].insert(0, stats[s])
        for a in self.ATTR_RUS.keys():
            if save_p and save_p[a]: self.checkboxes[f"save_{a}"].select()
            else: self.checkboxes[f"save_{a}"].deselect()
        for sk in self.SKILL_ATTR_MAP.keys():
            if skill_p and skill_p[sk]: self.checkboxes[f"skill_{sk}"].select()
            else: self.checkboxes[f"skill_{sk}"].deselect()
        notes_text = char['Notes'] if char['Notes'] else ''
        self.entries["notes"].delete("1.0", "end")
        if notes_text: self.entries["notes"].insert("1.0", notes_text)
        self._recalculate()

    def _on_stat_change(self):
        try:
            xp = int(self.entries["experience"].get().strip() or 0)
            ld = self.db.fetchone("SELECT Level, ProficiencyBonus FROM `experiencelevelmap` WHERE user_id = %s AND MinExperience <= %s ORDER BY MinExperience DESC LIMIT 1", (self.user_id, xp))
            if ld:
                for k, db_key in [("level", "Level"), ("prof_bonus", "ProficiencyBonus")]:
                    self.entries[k].configure(state="normal"); self.entries[k].delete(0, "end"); self.entries[k].insert(0, ld[db_key])
        except ValueError: pass
        self._recalculate()

    def _recalculate(self):
        if not self.current_char_id: return
        try:
            pb = int(self.entries["prof_bonus"].get().strip() or 2)
            for a in self.ATTR_RUS.keys():
                sc = int(self.entries[f"{a}_score"].get().strip() or 10); self.entries[f"{a}_mod"].configure(text=f"{DiceEngine.calc_modifier(sc):+d}")
            dx = DiceEngine.calc_modifier(int(self.entries["Dexterity_score"].get().strip() or 10))
            self.entries["Initiative"].configure(state="normal"); self.entries["Initiative"].delete(0, "end"); self.entries["Initiative"].insert(0, dx); self.entries["Initiative"].configure(state="readonly")
            for a in self.ATTR_RUS.keys():
                m = DiceEngine.calc_modifier(int(self.entries[f"{a}_score"].get().strip() or 10)); p = 1 if self.checkboxes[f"save_{a}"].get() else 0
                self.entries[f"save_{a}_total"].configure(text=f"{m + pb*p:+d}")
            for sk, a in self.SKILL_ATTR_MAP.items():
                m = DiceEngine.calc_modifier(int(self.entries[f"{a}_score"].get().strip() or 10)); p = 1 if self.checkboxes[f"skill_{sk}"].get() else 0
                self.entries[f"skill_{sk}_total"].configure(text=f"{m + pb*p:+d}")
        except Exception as e: print(f"Ошибка расчёта: {e}")

    def _save_all(self):
        if not self.current_char_id: return
        try:
            cid = self.current_char_id
            self.db.execute("UPDATE `character` SET Race=%s, Class=%s, Experience=%s, Level=%s, ProficiencyBonus=%s WHERE idCharacter=%s AND user_id=%s",
                (self.entries["race"].get().strip(), self.entries["class_"].get().strip(), int(self.entries["experience"].get().strip() or 0), int(self.entries["level"].get().strip() or 1), int(self.entries["prof_bonus"].get().strip() or 2), cid, self.user_id))
            attrs = list(self.ATTR_RUS.keys())
            scores = tuple(int(self.entries[f"{a}_score"].get().strip() or 10) for a in attrs)
            self.db.execute(f"UPDATE `attribute` SET {','.join(f'{a}=%s' for a in attrs)} WHERE idCharacter=%s", scores + (cid,))
            stats_cols = ["MaxHP", "CurrentHP", "ArmorClass", "Speed"]
            stats_vals = tuple(int(self.entries[c].get().strip() or 10) for c in stats_cols)
            self.db.execute(f"UPDATE `characterstats` SET {','.join(f'{c}=%s' for c in stats_cols)} WHERE idCharacter=%s", stats_vals + (cid,))
            for a in attrs: self.db.execute(f"UPDATE `savingthrowsproficiency` SET {a}=%s WHERE idCharacter=%s", (1 if self.checkboxes[f"save_{a}"].get() else 0, cid))
            for sk in self.SKILL_ATTR_MAP.keys(): self.db.execute(f"UPDATE `skillproficiency` SET {sk}=%s WHERE idCharacter=%s", (1 if self.checkboxes[f"skill_{sk}"].get() else 0, cid))
            pb = int(self.entries["prof_bonus"].get().strip() or 2)
            save_vals, skill_vals = [], []
            for a in attrs:
                score = int(self.entries[f"{a}_score"].get().strip() or 10); mod = DiceEngine.calc_modifier(score); prof = 1 if self.checkboxes[f"save_{a}"].get() else 0
                save_vals.append(mod + pb * prof)
            for sk, a in self.SKILL_ATTR_MAP.items():
                score = int(self.entries[f"{a}_score"].get().strip() or 10); mod = DiceEngine.calc_modifier(score); prof = 1 if self.checkboxes[f"skill_{sk}"].get() else 0
                skill_vals.append(mod + pb * prof)
            self.db.execute(f"UPDATE `savingthrows` SET {','.join(f'{a}=%s' for a in attrs)} WHERE idCharacter=%s", tuple(save_vals) + (cid,))
            self.db.execute(f"UPDATE `skill` SET {','.join(f'{sk}=%s' for sk in self.SKILL_ATTR_MAP.keys())} WHERE idCharacter=%s", tuple(skill_vals) + (cid,))
            notes_content = self.entries["notes"].get("1.0", "end").strip()
            self.db.execute("UPDATE `character` SET Notes = %s WHERE idCharacter = %s AND user_id = %s", (notes_content, cid, self.user_id))
            self.db.commit()
            self._notify("✅ Сохранено", "Данные персонажа успешно обновлены!")
            self.parent_window.after(600, self.parent_window.destroy)
        except Exception as e: self._notify("❌ Ошибка сохранения", str(e), "red")

    def _notify(self, title, msg, color="#2ECC71"):
        d = ctk.CTkToplevel(self.parent_window); d.title(title); d.geometry("260x100")
        d.transient(self.parent_window); d.grab_set(); d.attributes("-topmost", True); d.lift()
        d.geometry(f"260x100+{self.parent_window.winfo_rootx()+(self.parent_window.winfo_width()//2)-130}+{self.parent_window.winfo_rooty()+(self.parent_window.winfo_height()//2)-50}")
        ctk.CTkLabel(d, text=msg, text_color=color).pack(pady=15); ctk.CTkButton(d, text="OK", command=d.destroy, width=70).pack(); d.after(1500, d.destroy)