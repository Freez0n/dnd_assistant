import customtkinter as ctk
from app.database import DatabaseManager
from datetime import datetime

class NotesView(ctk.CTkFrame):
    CATEGORIES = ["Сюжет", "НПС", "Локации", "Фракции", "Секреты", "Прочее"]
    
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int):
        super().__init__(parent); self.db = db; self.user_id = user_id; self.current_note_id: int = None
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1)
        tree_frame = ctk.CTkFrame(self, width=200); tree_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        ctk.CTkLabel(tree_frame, text="Разделы", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.category_buttons = {}
        for cat in self.CATEGORIES:
            btn = ctk.CTkButton(tree_frame, text=cat, width=180, anchor="w", command=lambda c=cat: self._filter_by_category(c))
            btn.pack(pady=2); self.category_buttons[cat] = btn
        ctk.CTkButton(tree_frame, text="Все заметки", width=180, command=self._load_all_notes).pack(pady=10)
        ctk.CTkButton(tree_frame, text="+ Новая заметка", width=180, fg_color="#2ECC71", command=self._create_note).pack(pady=5)
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(tree_frame, placeholder_text="Поиск...", textvariable=self.search_var)
        search_entry.pack(pady=5, padx=5); search_entry.bind("<KeyRelease>", lambda e: self._search_notes())
        
        list_frame = ctk.CTkFrame(self); list_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(list_frame, text="Заметки", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.notes_scroll = ctk.CTkScrollableFrame(list_frame); self.notes_scroll.pack(fill="both", expand=True, pady=5)
        self.note_items = {}; self._load_all_notes()
        
        editor_container = ctk.CTkFrame(self); editor_container.grid(row=1, column=0, columnspan=2, sticky="ew", padx=40, pady=10)
        ctk.CTkLabel(editor_container, text="✏️ Редактор заметки", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=(5, 10))
        meta_frame = ctk.CTkFrame(editor_container, fg_color="transparent"); meta_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(meta_frame, text="Заголовок: ").pack(side="left", padx=10); self.title_entry = ctk.CTkEntry(meta_frame, width=300); self.title_entry.pack(side="left", padx=5)
        ctk.CTkLabel(meta_frame, text="Категория: ").pack(side="left", padx=(20, 5)); self.category_var = ctk.StringVar(value="Прочее")
        ctk.CTkOptionMenu(meta_frame, values=self.CATEGORIES, variable=self.category_var, width=120).pack(side="left", padx=5)
        ctk.CTkLabel(editor_container, text="Текст заметки: ").pack(anchor="w", padx=45, pady=(10, 0))
        self.body_text = ctk.CTkTextbox(editor_container, height=120, width=700); self.body_text.pack(pady=5, padx=40)
        btn_frame = ctk.CTkFrame(editor_container,  fg_color="transparent"); btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self._save_note, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="️ Удалить", command=self._delete_note, width=100, fg_color="#E74C3C").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📄 Экспорт в .txt", command=self._export_txt, width=120).pack(side="left", padx=10)

    def _load_all_notes(self): self._load_notes()
    def _filter_by_category(self, category: str): self._load_notes(category)
    
    def _load_notes(self, category: str = None):
        for widget in self.notes_scroll.winfo_children(): widget.destroy(); self.note_items = {}
        query = "SELECT * FROM `note` WHERE user_id = %s"; params = [self.user_id]
        if category: query += " AND Category = %s"; params.append(category)
        query += " ORDER BY UpdatedAt DESC"; notes = self.db.fetchall(query, tuple(params))
        for note in notes:
            item = ctk.CTkFrame(self.notes_scroll); item.pack(fill="x", pady=2)
            ctk.CTkLabel(item, text=note['Title'], font=ctk.CTkFont(weight="bold"), width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"[{note['Category']}]", width=80, anchor="center").pack(side="left", padx=5)
            ctk.CTkLabel(item, text=note['UpdatedAt'], width=100, anchor="center").pack(side="left", padx=5)
            ctk.CTkButton(item, text="Открыть", width=70, height=24, command=lambda n=note: self._open_note(n)).pack(side="right", padx=5)
            self.note_items[note['idNote']] = item

    def _search_notes(self):
        term = self.search_var.get().lower()
        for widget in self.notes_scroll.winfo_children(): widget.pack_forget()
        notes = self.db.fetchall("SELECT * FROM `note` WHERE user_id = %s ORDER BY UpdatedAt DESC", (self.user_id,))
        for note in notes:
            if term in note['Title'].lower() or term in note['Body'].lower(): self.note_items[note['idNote']].pack(fill="x", pady=2)

    def _open_note(self, note: dict):
        self.current_note_id = note['idNote']; self.title_entry.delete(0, "end"); self.title_entry.insert(0, note['Title'])
        self.category_var.set(note['Category']); self.body_text.delete("1.0", "end"); self.body_text.insert("1.0", note['Body'] or '')

    def _create_note(self): self.current_note_id = None; self.title_entry.delete(0, "end"); self.category_var.set("Прочее"); self.body_text.delete("1.0", "end")
    
    def _save_note(self):
        title = self.title_entry.get().strip(); body = self.body_text.get("1.0", "end").strip(); category = self.category_var.get()
        if not title: return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.current_note_id:
            self.db.execute("UPDATE `note` SET Title=%s, Body=%s, Category=%s, UpdatedAt=%s WHERE idNote=%s AND user_id=%s", (title, body, category, now, self.current_note_id, self.user_id))
        else:
            self.db.execute("INSERT INTO `note` (user_id, Title, Body, Category, CreatedAt, UpdatedAt) VALUES (%s, %s, %s, %s, %s, %s)", (self.user_id, title, body, category, now, now))
            self.current_note_id = self.db.last_insert_id()
        self.db.commit(); self._load_all_notes()

    def _delete_note(self):
        if not self.current_note_id: return
        dialog = ctk.CTkToplevel(self); dialog.title("Подтверждение"); dialog.geometry("300x120")
        self._center_window(dialog, 300, 120); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text="Удалить заметку?").pack(pady=15)
        def confirm(): 
            self.db.execute("DELETE FROM `note` WHERE idNote = %s AND user_id = %s", (self.current_note_id, self.user_id))
            self.db.commit(); self._create_note(); self._load_all_notes(); dialog.destroy()
        ctk.CTkButton(dialog, text="Да", fg_color="#E74C3C", command=confirm).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(dialog, text="Нет", command=dialog.destroy).pack(side="right", padx=20, pady=10)

    def _export_txt(self):
        title = self.title_entry.get().strip() or "Заметка"; body = self.body_text.get("1.0", "end")
        try:
            with open(f"{title}.txt", "w", encoding="utf-8") as f: f.write(f"Заголовок: {title}\nКатегория: {self.category_var.get()}\nДата: {datetime.now().strftime('%Y-%m-%d')}\n\n{body}")
        except Exception as e: print(f"Ошибка экспорта: {e}")

    def _center_window(self, window, width, height):
        window.update_idletasks(); x = (window.winfo_screenwidth() // 2) - (width // 2); y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')