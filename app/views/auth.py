import customtkinter as ctk
from app.auth import register_user, login_user
from app.database import DatabaseManager

class AuthWindow(ctk.CTkToplevel):
    def __init__(self, parent, db: DatabaseManager, on_login_success):
        super().__init__(parent)
        self.db = db
        self.on_login_success = on_login_success
        self.title("🐉 D&D Assistant — Вход")
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(parent); self.grab_set()
        
        self.container = ctk.CTkFrame(self); self.container.pack(fill="both", expand=True, padx=30, pady=30)
        self._build_login()

    def _clear(self):
        for w in self.container.winfo_children(): w.destroy()

    def _show_error(self, msg):
        for w in self.container.winfo_children():
            if isinstance(w, ctk.CTkLabel) and "" in w.cget("text"): w.destroy()
        ctk.CTkLabel(self.container, text=f" {msg}", text_color="#E74C3C", wraplength=340).pack(pady=5)

    def _build_login(self):
        self._clear()
        ctk.CTkLabel(self.container, text="🐉 Вход", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=15)
        
        self.login_entry = ctk.CTkEntry(self.container, placeholder_text="Логин", width=320, height=40); self.login_entry.pack(pady=8)
        self.pass_entry = ctk.CTkEntry(self.container, placeholder_text="Пароль", show="*", width=320, height=40); self.pass_entry.pack(pady=8)
        
        ctk.CTkButton(self.container, text="Войти", command=self._do_login, width=320, height=40, fg_color="#2ECC71", font=ctk.CTkFont(weight="bold")).pack(pady=20)
        ctk.CTkButton(self.container, text="Нет аккаунта? Зарегистрироваться", command=self._build_register, width=320, height=30, fg_color="transparent").pack(pady=5)

    def _do_login(self):
        username, pwd = self.login_entry.get().strip(), self.pass_entry.get()
        if not (username and pwd): self._show_error("Заполните все поля"); return
        
        result = login_user(self.db, username, pwd)
        if result['success']:
            self.on_login_success(result['user']['id'])
            self.destroy()
        else:
            self._show_error(result['error'])

    def _build_register(self):
        self._clear()
        ctk.CTkLabel(self.container, text="📝 Регистрация", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=15)
        
        self.reg_user = ctk.CTkEntry(self.container, placeholder_text="Придумайте логин", width=320, height=40); self.reg_user.pack(pady=8)
        self.reg_pass = ctk.CTkEntry(self.container, placeholder_text="Придумайте пароль", show="*", width=320, height=40); self.reg_pass.pack(pady=8)
        self.reg_pass2 = ctk.CTkEntry(self.container, placeholder_text="Повторите пароль", show="*", width=320, height=40); self.reg_pass2.pack(pady=8)
        
        ctk.CTkButton(self.container, text="Зарегистрироваться", command=self._do_register, width=320, height=40, fg_color="#2ECC71", font=ctk.CTkFont(weight="bold")).pack(pady=20)
        ctk.CTkButton(self.container, text="← Назад ко входу", command=self._build_login, width=320, height=30, fg_color="transparent").pack(pady=5)

    def _do_register(self):
        username = self.reg_user.get().strip()
        pwd1, pwd2 = self.reg_pass.get(), self.reg_pass2.get()
        
        if not (username and pwd1 and pwd2): self._show_error("Заполните все поля"); return
        if len(pwd1) < 6: self._show_error("Пароль должен быть не менее 6 символов"); return
        if pwd1 != pwd2: self._show_error("Пароли не совпадают"); return
            
        result = register_user(self.db, username, pwd1)
        if result['success']:
            self._show_error("")
            ctk.CTkLabel(self.container, text="✅ Аккаунт создан! Войдите.", text_color="#2ECC71").pack(pady=10)
            self.after(1500, self._build_login)
        else:
            self._show_error(result['error'])