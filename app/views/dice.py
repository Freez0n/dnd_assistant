import customtkinter as ctk
from app.database import DatabaseManager
from app.utils.dice_engine import DiceEngine
from datetime import datetime
import re

class DiceView(ctk.CTkFrame):
    MAX_DICE_LIMIT = 1000
    
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int):
        super().__init__(parent); self.db = db; self.user_id = user_id; self.current_dice_sides = 20
        self.grid_rowconfigure(0, weight=0); self.grid_rowconfigure(1, weight=0); self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=3); self.grid_rowconfigure(4, weight=1); self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        dice_frame = ctk.CTkFrame(self); dice_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(dice_frame, text="🎲 Бросок костей", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        dice_buttons = ctk.CTkFrame(dice_frame, fg_color="transparent"); dice_buttons.pack(pady=5)
        for sides in [4, 6, 8, 10, 12, 20, 100]:
            btn = ctk.CTkButton(dice_buttons, text=f"d{sides}", width=60, command=lambda s=sides: self._set_dice(s)); btn.pack(side="left", padx=3)
            if sides == 20: self.current_dice_sides = sides
            
        settings_frame = ctk.CTkFrame(self); settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        qty_frame = ctk.CTkFrame(settings_frame, fg_color="transparent"); qty_frame.pack(side="left", padx=10)
        ctk.CTkLabel(qty_frame, text="Количество (макс 1000): ").pack(side="left", padx=5)
        self.count_entry = ctk.CTkEntry(qty_frame, width=70); self.count_entry.insert(0, "1"); self.count_entry.pack(side="left", padx=5)
        self.count_entry.bind("<KeyRelease>", lambda e: self._update_formula())
        mod_frame = ctk.CTkFrame(settings_frame, fg_color="transparent"); mod_frame.pack(side="left", padx=10)
        ctk.CTkLabel(mod_frame, text="Модификатор: ").pack(side="left", padx=5)
        self.mod_entry = ctk.CTkEntry(mod_frame, width=60); self.mod_entry.insert(0, "0"); self.mod_entry.pack(side="left", padx=5)
        self.mod_entry.bind("<KeyRelease>", lambda e: self._update_formula())
        adv_frame = ctk.CTkFrame(settings_frame, fg_color="transparent"); adv_frame.pack(side="left", padx=10)
        self.advantage_var = ctk.BooleanVar(); self.disadvantage_var = ctk.BooleanVar()
        self.adv_cb = ctk.CTkCheckBox(adv_frame, text="✅ Преимущество", variable=self.advantage_var, command=self._on_advantage_change, checkbox_width=18, checkbox_height=18); self.adv_cb.pack(side="left", padx=3)
        self.disadv_cb = ctk.CTkCheckBox(adv_frame, text="⚠️ Помеха", variable=self.disadvantage_var, command=self._on_disadvantage_change, checkbox_width=18, checkbox_height=18); self.disadv_cb.pack(side="left", padx=3)
        ctk.CTkLabel(settings_frame, text="💡 Преимущество/помеха работают только для d20", font=ctk.CTkFont(size=10), text_color="#888").pack(side="left", padx=15)
        
        formula_frame = ctk.CTkFrame(self); formula_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(formula_frame, text="Формула: ").pack(anchor="w", padx=5, pady=(5, 0))
        self.formula_entry = ctk.CTkEntry(formula_frame, height=40, font=ctk.CTkFont(size=14)); self.formula_entry.insert(0, "1d20"); self.formula_entry.pack(fill="x", padx=5, pady=5)
        btn_row = ctk.CTkFrame(formula_frame, fg_color="transparent"); btn_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(btn_row, text=" БРОСИТЬ!", command=self._roll, width=140, height=38, fg_color="#2ECC71", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="💾 Сохранить формулу", command=self._save_formula, width=140, height=38).pack(side="left", padx=5)
        
        result_frame = ctk.CTkFrame(self); result_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=15)
        # Исправлено: уменьшен размер шрифта и добавлен перенос строк
        self.result_label = ctk.CTkLabel(
            result_frame, 
            text="—", 
            font=ctk.CTkFont(size=40, weight="bold"), 
            text_color="#2ECC71",
            wraplength=700,
            justify="center"
        )
        self.result_label.pack(fill="both", expand=True, pady=20)
        self.mode_label = ctk.CTkLabel(result_frame, text="", font=ctk.CTkFont(size=14, weight="bold")); self.mode_label.pack(pady=5)
        
        history_frame = ctk.CTkFrame(self); history_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(history_frame, text="📜 История бросков", font=ctk.CTkFont(weight="bold")).pack()
        self.history_text = ctk.CTkTextbox(history_frame, height=140); self.history_text.pack(fill="both", expand=True, pady=5, padx=5); self._load_history()
        
        saved_frame = ctk.CTkFrame(self); saved_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(saved_frame, text="💾 Библиотека формул", font=ctk.CTkFont(weight="bold")).pack()
        self.saved_list = ctk.CTkScrollableFrame(saved_frame, height=100); self.saved_list.pack(fill="x", pady=5); self._load_saved_formulas()

    def _on_advantage_change(self):
        if self.advantage_var.get(): self.disadvantage_var.set(False); self.mode_label.configure(text="🟢 Режим: Преимущество", text_color="#2ECC71")
        else: self.mode_label.configure(text="")
    def _on_disadvantage_change(self):
        if self.disadvantage_var.get(): self.advantage_var.set(False); self.mode_label.configure(text="🔴 Режим: Помеха", text_color="#E74C3C")
        else: self.mode_label.configure(text="")
    def _set_dice(self, sides: int):
        self.current_dice_sides = sides; self._update_formula()
        if sides != 20: self.advantage_var.set(False); self.disadvantage_var.set(False); self.mode_label.configure(text="")
    def _update_formula(self):
        count = self.count_entry.get().strip() or "1"; mod = self.mod_entry.get().strip()
        try: count = int(count)
        except: count = 1
        if count > self.MAX_DICE_LIMIT: count = self.MAX_DICE_LIMIT; self.count_entry.delete(0, "end"); self.count_entry.insert(0, str(self.MAX_DICE_LIMIT))
        elif count < 1: count = 1; self.count_entry.delete(0, "end"); self.count_entry.insert(0, "1")
        formula = f"{count}d{self.current_dice_sides}"
        if mod and mod != "0" and mod != "-0": formula += mod if mod.startswith("-") else f"+{mod}"
        self.formula_entry.delete(0, "end"); self.formula_entry.insert(0, formula)

    def _roll(self):
        formula = self.formula_entry.get().strip()
        if not formula: return
        match = re.match(r'(\d+)d(\d+)([+-]\d+)?', formula)
        if match:
            count = int(match.group(1))
            if count > self.MAX_DICE_LIMIT:
                self.result_label.configure(text=f"⚠️ Макс. {self.MAX_DICE_LIMIT}!", text_color="#E74C3C"); self.mode_label.configure(text="Превышен лимит кубов!", text_color="red"); return
        advantage = self.advantage_var.get(); disadvantage = self.disadvantage_var.get()
        self.result_label.configure(text="🎲", text_color="#F39C12"); self.mode_label.configure(text="Бросаем..."); self.update_idletasks()
        result, details, original_formula = DiceEngine.roll_formula(formula, advantage, disadvantage)
        self.result_label.configure(text=str(result), text_color="#2ECC71")
        if advantage: self.mode_label.configure(text="🟢 Преимущество применено", text_color="#2ECC71")
        elif disadvantage: self.mode_label.configure(text=" Помеха применена", text_color="#E74C3C")
        else: self.mode_label.configure(text="")
        try:
            self.db.execute("INSERT INTO `dicerollhistory` (user_id, Formula, Result, Details) VALUES (%s, %s, %s, %s)", 
                            (self.user_id, f"{original_formula} [{'преимущество' if advantage else 'помеха' if disadvantage else 'обычный'}]", result, details))
            self.db.commit(); self._load_history()
        except Exception as e: print(f"Ошибка сохранения истории: {e}")

    def _load_history(self):
        self.history_text.configure(state="normal"); self.history_text.delete("1.0", "end")
        try:
            rolls = self.db.fetchall("SELECT Formula, Result, Details, Timestamp FROM `dicerollhistory` WHERE user_id = %s ORDER BY idRoll DESC LIMIT 30", (self.user_id,))
            if not rolls: self.history_text.insert("1.0", "История пуста. Сделайте первый бросок! ")
            else:
                for i, roll in enumerate(rolls):
                    f = roll['Formula']
                    if '[преимущество]' in f: f = f.replace('[преимущество]', '🟢преимущество')
                    elif '[помеха]' in f: f = f.replace('[помеха]', '🔴помеха🔴')
                    self.history_text.insert("end", f"#{i+1} | {roll['Timestamp']} | {f}\n")
                    if roll['Details']: self.history_text.insert("end", f"    {roll['Details']}\n")
                    self.history_text.insert("end", f"   ➤ Итог: {roll['Result']}\n\n")
        except Exception as e: self.history_text.insert("1.0", f"Ошибка загрузки: {e}")
        self.history_text.configure(state="disabled")

    def _load_saved_formulas(self):
        for widget in self.saved_list.winfo_children(): widget.destroy()
        try:
            formulas = self.db.fetchall("SELECT * FROM `saveddiceformula` WHERE user_id = %s ORDER BY Name", (self.user_id,))
            for f in formulas:
                frame = ctk.CTkFrame(self.saved_list); frame.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(frame, text=f['Name'], width=120, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(frame, text=f['Formula'], width=100, anchor="w").pack(side="left", padx=5)
                btn_f = ctk.CTkFrame(frame, fg_color="transparent"); btn_f.pack(side="right", padx=5)
                ctk.CTkButton(btn_f, text="Использовать", width=80, height=26, command=lambda formula=f['Formula']: self._use_saved_formula(formula)).pack(side="left", padx=2)
                ctk.CTkButton(btn_f, text="✕", width=26, height=26, fg_color="#E74C3C", command=lambda fid=f['idFormula']: self._delete_formula(fid)).pack(side="left", padx=2)
        except Exception as e: print(f"Ошибка загрузки формул: {e}")

    def _use_saved_formula(self, formula: str):
        self.formula_entry.delete(0, "end")
        self.formula_entry.insert(0, formula)
    
        match = re.fullmatch(r'(\d+)d(\d+)([+-]\d+)?', formula)
    
        if match:
            self.count_entry.delete(0, "end")
            self.count_entry.insert(0, match.group(1))
            self.current_dice_sides = int(match.group(2))
        
            mod_value = match.group(3) or "0"
            if mod_value.startswith("+"):
                mod_value = mod_value[1:] 
        
            self.mod_entry.delete(0, "end")
            self.mod_entry.insert(0, mod_value)
            self._update_formula()
        else:
            self.count_entry.delete(0, "end")
            self.count_entry.insert(0, "1")
            self.mod_entry.delete(0, "end")
            self.mod_entry.insert(0, "0")

    def _save_formula(self):
        formula = self.formula_entry.get().strip()
        if not formula: return
        dialog = ctk.CTkToplevel(self); dialog.title("Сохранить формулу"); dialog.geometry("350x150")
        self._center_window(dialog, 350, 150); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text="Название формулы: ").pack(pady=10); name_entry = ctk.CTkEntry(dialog, width=280); name_entry.pack(pady=5)
        def save():
            name = name_entry.get().strip()
            if name:
                try: 
                    self.db.execute("INSERT INTO `saveddiceformula` (user_id, Name, Formula) VALUES (%s, %s, %s)", (self.user_id, name, formula))
                    self.db.commit(); self._load_saved_formulas(); dialog.destroy()
                except Exception as e: print(f"Ошибка: {e}")
        ctk.CTkButton(dialog, text="Сохранить", command=save).pack(pady=10)

    def _delete_formula(self, formula_id: int):
        try: 
            self.db.execute("DELETE FROM `saveddiceformula` WHERE idFormula = %s AND user_id = %s", (formula_id, self.user_id))
            self.db.commit(); self._load_saved_formulas()
        except Exception as e: print(f"Ошибка удаления: {e}")

    def _center_window(self, window, width, height):
        window.update_idletasks(); x = (window.winfo_screenwidth() // 2) - (width // 2); y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')