import customtkinter as ctk
from app.database import DatabaseManager
from app.auth import change_password, clear_session

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTk, db: DatabaseManager, campaign_name_callback, user_id: int, on_logout):
        super().__init__(parent)
        self.db = db; self.user_id = user_id; self.on_logout = on_logout
        self.campaign_name_callback = campaign_name_callback
        
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        content = ctk.CTkScrollableFrame(self); content.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)

        ctk.CTkLabel(content, text=" Название кампании", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.campaign_entry = ctk.CTkEntry(content, width=300, placeholder_text="Введите название...")
        saved_name = self.db.get_config("campaign_name", "")
        if saved_name: self.campaign_entry.insert(0, saved_name)
        self.campaign_entry.pack(pady=5)
        ctk.CTkButton(content, text=" Сохранить", command=self._save_campaign_name, width=100).pack(pady=5)

        ctk.CTkLabel(content, text="👤 Управление аккаунтом", font=ctk.CTkFont(weight="bold")).pack(pady=(30, 5))
        
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="🔄 Сменить пароль", command=self._change_password_dialog, width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=" Выйти из аккаунта", command=self._logout, width=150, fg_color="#E74C3C").pack(side="left", padx=5)

        ctk.CTkLabel(content, text="️ Личные данные", font=ctk.CTkFont(weight="bold"), text_color="#E74C3C").pack(pady=(30, 5))
        ctk.CTkLabel(content, text="Удалить ВСЕ ваши персонажи, заметки и предметы?").pack(pady=2)
        ctk.CTkButton(content, text="🗑️ УДАЛИТЬ МОИ ДАННЫЕ", command=self._confirm_reset_user_data, 
                      width=220, fg_color="#E74C3C", hover_color="#C0392B").pack(pady=10)

        ctk.CTkLabel(content, text="ℹ️ О приложении", font=ctk.CTkFont(weight="bold")).pack(pady=(30, 5))
        ctk.CTkLabel(content, text="🐉 Ассистент Мастера Подземелий D&D 5e").pack()
        ctk.CTkLabel(content, text="Версия: Демонстрационая").pack()

    def _save_campaign_name(self):
        name = self.campaign_entry.get().strip()
        if name and self.campaign_name_callback:
            self.db.set_config("campaign_name", name); self.campaign_name_callback(name)

    def _change_password_dialog(self):
        dialog = ctk.CTkToplevel(self); dialog.title("Смена пароля"); dialog.geometry("350x300")
        self._center_window(dialog, 350, 300); dialog.transient(self); dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Текущий пароль:").pack(pady=(20, 5))
        old_entry = ctk.CTkEntry(dialog, show="*", width=280); old_entry.pack(pady=5)
        ctk.CTkLabel(dialog, text="Новый пароль (мин. 6 символов):").pack(pady=(10, 5))
        new_entry = ctk.CTkEntry(dialog, show="*", width=280); new_entry.pack(pady=5)
        
        msg_label = ctk.CTkLabel(dialog, text="", text_color="red")
        msg_label.pack(pady=10)

        def do_change():
            res = change_password(self.db, self.user_id, old_entry.get(), new_entry.get())
            if res['success']:
                msg_label.configure(text="✅ Пароль успешно изменён!", text_color="#2ECC71")
                dialog.after(1500, dialog.destroy)
            else:
                msg_label.configure(text=f"❌ {res['error']}")

        ctk.CTkButton(dialog, text="Сохранить", command=do_change, fg_color="#2ECC71").pack(pady=10)

    def _logout(self):
        clear_session()
        self.on_logout()

    def _confirm_reset_user_data(self):
        dialog = ctk.CTkToplevel(self); dialog.title("️ ПОДТВЕРДИТЕ"); dialog.geometry("400x200")
        self._center_window(dialog, 400, 200); dialog.transient(self); dialog.grab_set()
        ctk.CTkLabel(dialog, text="Вы уверены?\nВсе ВАШИ персонажи, монстры и заметки будут удалены!\nГлобальный бестиарий останется.", 
                     text_color="#E74C3C", justify="center", font=ctk.CTkFont(weight="bold")).pack(pady=15)
        
        def do_reset():
            tables_with_user_id = [
                "combatsession", 
                "note", 
                "item", 
                "character",
                "monster", 
                "dicerollhistory", 
                "saveddiceformula"
            ]
            
            try:
                for table in tables_with_user_id:
                    self.db.execute(f"DELETE FROM `{table}` WHERE user_id = %s", (self.user_id,))
                self.db.commit()
                
                dialog.destroy()
                msg = ctk.CTkToplevel(self); msg.title("✅ Готово"); msg.geometry("300x120")
                self._center_window(msg, 300, 120); msg.transient(self); msg.grab_set()
                ctk.CTkLabel(msg, text="Ваши данные успешно очищены.").pack(pady=25)
                ctk.CTkButton(msg, text="OK", command=msg.destroy, width=100).pack()
            except Exception as e:
                print(f"Ошибка при сбросе данных: {e}")

        ctk.CTkButton(dialog, text="️ УДАЛИТЬ", fg_color="#E74C3C", command=do_reset).pack(pady=10)
        ctk.CTkButton(dialog, text="Отмена", command=dialog.destroy).pack()

    def _center_window(self, window, width, height):
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')