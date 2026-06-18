import customtkinter as ctk
from app.database import DatabaseManager
from app.utils.generators import Generators

class TreasuryView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, user_id: int):
        super().__init__(parent); self.db = db; self.user_id = user_id
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        control_frame = ctk.CTkFrame(self); control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(control_frame, text="💰 Сокровищница", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="+ Добавить предмет", command=self._add_item_dialog, width=140).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Генератор сокровищ", command=self._generate_treasure, width=140, fg_color="#9B59B6").pack(side="left", padx=5)
        ctk.CTkLabel(control_frame, text="Фильтр: ").pack(side="left", padx=(20, 5))
        self.type_var = ctk.StringVar(value="Все")
        ctk.CTkOptionMenu(control_frame, values=["Все", "Оружие", "Доспех", "Зелье", "Свиток", "Чудо-предмет", "Кольцо", "Посох"], variable=self.type_var, width=120, command=self._filter_items).pack(side="left", padx=5)
        self.items_scroll = ctk.CTkScrollableFrame(self, label_text="Предметы"); self.items_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.item_rows = {}; self._load_items()

    def _load_items(self):
        for widget in self.items_scroll.winfo_children(): widget.destroy(); self.item_rows = {}
        query = "SELECT i.*, c.Name as owner_name FROM `item` i LEFT JOIN `character` c ON i.idOwner = c.idCharacter WHERE i.user_id = %s"; params = [self.user_id]
        if self.type_var.get() != "Все": query += " AND i.Type = %s"; params.append(self.type_var.get())
        items = [dict(row) for row in self.db.fetchall(query + " ORDER BY i.Name", tuple(params))]
        for item in items:
            row = ctk.CTkFrame(self.items_scroll); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=item['Name'], width=150, anchor="w").grid(row=0, column=0, padx=10)
            ctk.CTkLabel(row, text=item['Type'], width=100, anchor="center").grid(row=0, column=1, padx=5)
            ctk.CTkLabel(row, text=item['Rarity'], width=100, anchor="center").grid(row=0, column=2, padx=5)
            ctk.CTkLabel(row, text=item['owner_name'] if item['owner_name'] else "Без владельца", width=120, anchor="center").grid(row=0, column=3, padx=5)
            btn_frame = ctk.CTkFrame(row, fg_color="transparent"); btn_frame.grid(row=0, column=4, padx=5)
            ctk.CTkButton(btn_frame, text="✎", width=30, height=24, command=lambda it=item: self._edit_item(it)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="✕", width=30, height=24, fg_color="#E74C3C", command=lambda iid=item['idItem']: self._delete_item(iid)).pack(side="left", padx=2)
            self.item_rows[item['idItem']] = row

    def _filter_items(self, *args): self._load_items()
    def _add_item_dialog(self): self._open_item_dialog(None)
    def _edit_item(self, item: dict): self._open_item_dialog(item)

    def _open_item_dialog(self, item: dict):
        is_edit = item is not None
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактировать предмет" if is_edit else "Добавить предмет")
        dialog.geometry("500x600")
        self._center_window(dialog, 500, 600)
        dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        
        ctk.CTkLabel(dialog, text="Название предмета*", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        name_entry = ctk.CTkEntry(dialog, width=400, height=35)
        if is_edit and item.get('Name'): name_entry.insert(0, item['Name'])
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Тип предмета", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        type_var = ctk.StringVar(value="Прочее")
        type_menu = ctk.CTkOptionMenu(dialog, values=["Оружие", "Доспех", "Зелье", "Свиток", "Чудо-предмет", "Кольцо", "Посох", "Прочее"], variable=type_var, width=400)
        if is_edit and item.get('Type'): type_var.set(item['Type'])
        type_menu.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Редкость", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        rarity_var = ctk.StringVar(value="Обычный")
        rarity_menu = ctk.CTkOptionMenu(dialog, values=["Обычный", "Необычный", "Редкий", "Очень редкий", "Легендарный", "Артефакт"], variable=rarity_var, width=400)
        if is_edit and item.get('Rarity'): rarity_var.set(item['Rarity'])
        rarity_menu.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Описание", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        desc_text = ctk.CTkTextbox(dialog, width=400, height=100)
        if is_edit and item.get('Description'): desc_text.insert("1.0", item['Description'])
        desc_text.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Владелец (опционально)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        characters = self.db.fetchall("SELECT idCharacter, Name FROM `character` WHERE user_id = %s ORDER BY Name", (self.user_id,))
        owner_options = ["Без владельца"] + [c['Name'] for c in characters]
        owner_var = ctk.StringVar(value="Без владельца")
        owner_menu = ctk.CTkOptionMenu(dialog, values=owner_options, variable=owner_var, width=400)
        if is_edit and item.get('owner_name'): owner_var.set(item['owner_name'])
        owner_menu.pack(pady=5)
        
        def save():
            try:
                name = name_entry.get().strip()
                if not name:
                    ctk.CTkLabel(dialog, text="❌ Название обязательно!", text_color="red").pack(pady=5)
                    return
                
                item_type = type_var.get(); rarity = rarity_var.get()
                description = desc_text.get("1.0", "end").strip(); owner_name = owner_var.get()
                
                owner_id = None
                if owner_name != "Без владельца":
                    char = self.db.fetchone("SELECT idCharacter FROM `character` WHERE Name = %s AND user_id = %s", (owner_name, self.user_id))
                    if char: owner_id = char['idCharacter']
                
                if is_edit:
                    self.db.execute("""UPDATE `item` SET Name=%s, Type=%s, Rarity=%s, Description=%s, idOwner=%s 
                                    WHERE idItem=%s AND user_id=%s""", (name, item_type, rarity, description, owner_id, item['idItem'], self.user_id))
                else:
                    self.db.execute("INSERT INTO `item` (user_id, Name, Type, Rarity, Description, idOwner) VALUES (%s, %s, %s, %s, %s, %s)", 
                                   (self.user_id, name, item_type, rarity, description, owner_id))
                
                self.db.commit(); self._load_items(); dialog.destroy()
            except Exception as e:
                ctk.CTkLabel(dialog, text=f"❌ Ошибка: {str(e)}", text_color="red").pack(pady=5)
        
        ctk.CTkButton(dialog, text=" Сохранить", command=save, fg_color="#2ECC71", width=200, height=35, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)

    def _delete_item(self, item_id: int):
        dialog = ctk.CTkToplevel(self); dialog.title("Подтверждение"); dialog.geometry("300x120")
        self._center_window(dialog, 300, 120); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        ctk.CTkLabel(dialog, text="Удалить предмет?").pack(pady=15)
        def confirm(): 
            self.db.execute("DELETE FROM `item` WHERE idItem = %s AND user_id = %s", (item_id, self.user_id))
            self.db.commit(); self._load_items(); dialog.destroy()
        ctk.CTkButton(dialog, text="Да", fg_color="#E74C3C", command=confirm).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(dialog, text="Нет", command=dialog.destroy).pack(side="right", padx=20, pady=10)

    def _generate_treasure(self):
        treasure = Generators.generate_treasure(); dialog = ctk.CTkToplevel(self); dialog.title("Сгенерированное сокровище"); dialog.geometry("500x400")
        self._center_window(dialog, 500, 400); dialog.transient(self); dialog.grab_set(); dialog.attributes("-topmost", True); dialog.lift()
        result_text = ctk.CTkTextbox(dialog, width=450, height=300); result_text.pack(pady=10, padx=10)
        result_text.insert("end", " Монеты:\n")
        for coin_type, amount in treasure['coins'].items():
            if amount > 0: result_text.insert("end", f"  • {amount} {coin_type}\n")
        if treasure['items']:
            result_text.insert("end", "\n🎁 Предметы:\n")
            for item in treasure['items']: result_text.insert("end", f"  • {item['name']} ({item['rarity']})\n    {item['description']}\n")
        result_text.configure(state="disabled")
        def add_to_db():
            for item in treasure['items']:
                self.db.execute("INSERT INTO `item` (user_id, Name, Type, Rarity, Description) VALUES (%s, %s, %s, %s, %s)", 
                               (self.user_id, item['name'], "Чудо-предмет", item['rarity'], item['description']))
            self.db.commit(); self._load_items(); dialog.destroy()
        ctk.CTkButton(dialog, text="Добавить предметы в базу", command=add_to_db).pack(pady=10)
        ctk.CTkButton(dialog, text="Закрыть", command=dialog.destroy).pack(pady=5)

    def _center_window(self, window, width, height):
        window.update_idletasks(); x = (window.winfo_screenwidth() // 2) - (width // 2); y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')